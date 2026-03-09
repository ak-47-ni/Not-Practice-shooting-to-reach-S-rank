from __future__ import annotations

import signal
import time
from threading import Event, Lock, Thread

from screen_human_lab.overlay.control import CursorFollowController, OverlayControl, should_toggle_for_characters
from screen_human_lab.overlay.state import OverlayState, build_detection_offset_label
from screen_human_lab.pipeline.gated_runtime import GatedDetectionRuntime


def compute_quartz_cursor_position(current_x: float, current_y: float, *, step_x: int, step_y: int) -> tuple[float, float]:
    return (current_x + float(step_x), current_y + float(step_y))


def compute_quartz_target_point(
    *,
    detection_bbox: tuple[int, int, int, int],
    monitor_left: int,
    monitor_top: int,
    monitor_width: int | None = None,
    monitor_height: int | None = None,
    screen_origin_x: float,
    screen_origin_y: float,
    screen_width: float | None = None,
    screen_height: float,
) -> tuple[float, float]:
    x1, y1, x2, y2 = detection_bbox
    target_center_x = (x1 + x2) / 2.0
    target_center_y = (y1 + y2) / 2.0
    return compute_quartz_screen_point(
        screen_x=target_center_x,
        screen_y=target_center_y,
        monitor_left=monitor_left,
        monitor_top=monitor_top,
        monitor_width=monitor_width,
        monitor_height=monitor_height,
        screen_origin_x=screen_origin_x,
        screen_origin_y=screen_origin_y,
        screen_width=screen_width,
        screen_height=screen_height,
    )


def compute_quartz_screen_point(
    *,
    screen_x: float,
    screen_y: float,
    monitor_left: int,
    monitor_top: int,
    monitor_width: int | None = None,
    monitor_height: int | None = None,
    screen_origin_x: float,
    screen_origin_y: float,
    screen_width: float | None = None,
    screen_height: float,
) -> tuple[float, float]:
    resolved_monitor_width = 1 if monitor_width is None else max(monitor_width, 1)
    resolved_monitor_height = 1 if monitor_height is None else max(monitor_height, 1)
    resolved_screen_width = float(resolved_monitor_width) if screen_width is None else max(screen_width, 1.0)
    resolved_screen_height = max(screen_height, 1.0)

    scale_x = resolved_screen_width / float(resolved_monitor_width)
    scale_y = resolved_screen_height / float(resolved_monitor_height)
    local_x = (screen_x - float(monitor_left)) * scale_x
    local_top = (screen_y - float(monitor_top)) * scale_y
    return (screen_origin_x + local_x, screen_origin_y + (resolved_screen_height - local_top))


def compute_quartz_screen_rect(
    *,
    rect_left: float,
    rect_top: float,
    rect_width: float,
    rect_height: float,
    monitor_left: int,
    monitor_top: int,
    monitor_width: int | None = None,
    monitor_height: int | None = None,
    screen_origin_x: float,
    screen_origin_y: float,
    screen_width: float | None = None,
    screen_height: float,
) -> tuple[float, float, float, float]:
    top_left_x, top_left_y = compute_quartz_screen_point(
        screen_x=rect_left,
        screen_y=rect_top,
        monitor_left=monitor_left,
        monitor_top=monitor_top,
        monitor_width=monitor_width,
        monitor_height=monitor_height,
        screen_origin_x=screen_origin_x,
        screen_origin_y=screen_origin_y,
        screen_width=screen_width,
        screen_height=screen_height,
    )
    bottom_right_x, bottom_right_y = compute_quartz_screen_point(
        screen_x=rect_left + rect_width,
        screen_y=rect_top + rect_height,
        monitor_left=monitor_left,
        monitor_top=monitor_top,
        monitor_width=monitor_width,
        monitor_height=monitor_height,
        screen_origin_x=screen_origin_x,
        screen_origin_y=screen_origin_y,
        screen_width=screen_width,
        screen_height=screen_height,
    )
    return (top_left_x, bottom_right_y, bottom_right_x - top_left_x, top_left_y - bottom_right_y)


def compute_quartz_overlay_rect(
    *,
    detection_bbox: tuple[int, int, int, int],
    roi_rect,
    overlay_width: float,
    overlay_height: float,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = detection_bbox
    resolved_overlay_width = max(float(overlay_width), 1.0)
    resolved_overlay_height = max(float(overlay_height), 1.0)
    scale_x = resolved_overlay_width / max(float(roi_rect.width), 1.0)
    scale_y = resolved_overlay_height / max(float(roi_rect.height), 1.0)
    local_x = (float(x1) - float(roi_rect.left)) * scale_x
    local_top = (float(y1) - float(roi_rect.top)) * scale_y
    width = max(float(x2 - x1) * scale_x, 1.0)
    height = max(float(y2 - y1) * scale_y, 1.0)
    return (local_x, resolved_overlay_height - local_top - height, width, height)


def get_macos_cursor_position(appkit_module) -> tuple[float, float]:
    point = appkit_module.NSEvent.mouseLocation()
    return (float(point.x), float(point.y))


def load_core_graphics_mouse_warp(objc_module):
    namespace: dict[str, object] = {}
    bundle = objc_module.loadBundle(
        "CoreGraphics",
        namespace,
        bundle_path=objc_module.pathForFramework("/System/Library/Frameworks/ApplicationServices.framework"),
    )
    objc_module.loadBundleFunctions(
        bundle,
        namespace,
        (("CGWarpMouseCursorPosition", b"i{CGPoint=dd}"),),
    )
    return namespace["CGWarpMouseCursorPosition"]


class MacOSCursorMover:
    def __init__(self, *, appkit_module, warp_mouse_cursor_position) -> None:
        self._appkit = appkit_module
        self._warp_mouse_cursor_position = warp_mouse_cursor_position

    def move_to(self, target_x: float, target_y: float) -> None:
        self._warp_mouse_cursor_position((float(target_x), float(target_y)))


class GatedDetectionWorker:
    def __init__(
        self,
        *,
        runtime: GatedDetectionRuntime,
        target_fps: int,
        initial_active: bool,
        cursor_follow_controller: CursorFollowController | None = None,
    ) -> None:
        self._runtime = runtime
        self._target_fps = max(target_fps, 1)
        self._cursor_follow_controller = cursor_follow_controller
        self._stop_event = Event()
        self._lock = Lock()
        self._active = initial_active
        self._thread: Thread | None = None
        self._has_cleared = False
        self._last_cursor_update_at: float | None = None
        self._cursor_follow_active = False

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = Thread(target=self._run_loop, name="screen-human-lab-gated-runtime", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def set_active(self, active: bool) -> None:
        with self._lock:
            self._active = active

    def _is_active(self) -> bool:
        with self._lock:
            return self._active

    def set_cursor_follow_active(self, active: bool) -> None:
        with self._lock:
            self._cursor_follow_active = active

    def _is_cursor_follow_active(self) -> bool:
        with self._lock:
            return self._cursor_follow_active

    def _run_loop(self) -> None:
        frame_interval = 1.0 / self._target_fps
        while not self._stop_event.is_set():
            active = self._is_active()
            if not active:
                if not self._has_cleared:
                    self._runtime.process_once(active=False)
                    self._has_cleared = True
                self._last_cursor_update_at = None
                time.sleep(0.01)
                continue

            started = time.perf_counter()
            result = self._runtime.process_once(active=True)
            cursor_update_at = time.perf_counter()
            if self._cursor_follow_controller is not None:
                delta_time = frame_interval if self._last_cursor_update_at is None else max(
                    cursor_update_at - self._last_cursor_update_at,
                    0.0,
                )
                self._cursor_follow_controller.update(
                    active=result.active and self._is_cursor_follow_active(),
                    roi_rect=result.roi_rect,
                    detections=result.detections,
                    delta_time=delta_time,
                )
            self._last_cursor_update_at = cursor_update_at
            self._has_cleared = False
            elapsed = time.perf_counter() - started
            remaining = frame_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)


def run_overlay_session(
    *,
    capture,
    backend,
    target_fps: int,
    infer_only_while_right_mouse_down: bool,
    cursor_follow_speed: float,
    cursor_follow_min_distance: float,
    tracker_factory=None,
) -> int:
    try:
        import AppKit
        from Foundation import NSObject, NSString
        from PyObjCTools import AppHelper
        import objc
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional dependency 'pyobjc-framework-Cocoa>=10.3' for macOS overlay mode"
        ) from exc

    warp_mouse_cursor_position = load_core_graphics_mouse_warp(objc)

    overlay_state = OverlayState(roi_rect=capture.roi_rect)
    control = OverlayControl()
    overlay_state.set_service_enabled(control.service_enabled)
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=tracker_factory,
    )
    screen_index = capture._config.monitor - 1
    screens = list(AppKit.NSScreen.screens())
    if screen_index >= len(screens):
        raise RuntimeError(f"No NSScreen is available for monitor index {capture._config.monitor}")
    screen = screens[screen_index]
    screen_frame = screen.frame()

    monitor_rect = capture.monitor_rect
    roi_rect = capture.roi_rect
    window_x, window_y, window_width, window_height = compute_quartz_screen_rect(
        rect_left=roi_rect.left,
        rect_top=roi_rect.top,
        rect_width=roi_rect.width,
        rect_height=roi_rect.height,
        monitor_left=monitor_rect.left,
        monitor_top=monitor_rect.top,
        monitor_width=monitor_rect.width,
        monitor_height=monitor_rect.height,
        screen_origin_x=float(screen_frame.origin.x),
        screen_origin_y=float(screen_frame.origin.y),
        screen_width=float(screen_frame.size.width),
        screen_height=float(screen_frame.size.height),
    )
    window_frame = AppKit.NSMakeRect(window_x, window_y, window_width, window_height)

    def _target_position_provider(detection, _roi_rect):
        return compute_quartz_target_point(
            detection_bbox=detection.bbox,
            monitor_left=monitor_rect.left,
            monitor_top=monitor_rect.top,
            monitor_width=monitor_rect.width,
            monitor_height=monitor_rect.height,
            screen_origin_x=float(screen_frame.origin.x),
            screen_origin_y=float(screen_frame.origin.y),
            screen_width=float(screen_frame.size.width),
            screen_height=float(screen_frame.size.height),
        )

    def _fallback_position_provider(roi_rect):
        return compute_quartz_screen_point(
            screen_x=roi_rect.left + (roi_rect.width / 2.0),
            screen_y=roi_rect.top + (roi_rect.height / 2.0),
            monitor_left=monitor_rect.left,
            monitor_top=monitor_rect.top,
            monitor_width=monitor_rect.width,
            monitor_height=monitor_rect.height,
            screen_origin_x=float(screen_frame.origin.x),
            screen_origin_y=float(screen_frame.origin.y),
            screen_width=float(screen_frame.size.width),
            screen_height=float(screen_frame.size.height),
        )

    worker = GatedDetectionWorker(
        runtime=runtime,
        target_fps=target_fps,
        initial_active=control.compute_active(
            right_mouse_down=False,
            infer_only_while_right_mouse_down=infer_only_while_right_mouse_down,
        ),
        cursor_follow_controller=CursorFollowController(
            mover=MacOSCursorMover(
                appkit_module=AppKit,
                warp_mouse_cursor_position=warp_mouse_cursor_position,
            ),
            cursor_position_provider=lambda: get_macos_cursor_position(AppKit),
            fallback_position_provider=_fallback_position_provider,
            target_position_provider=_target_position_provider,
            speed_pixels_per_second=cursor_follow_speed,
            min_distance=cursor_follow_min_distance,
        ),
    )

    class OverlayView(AppKit.NSView):
        def initWithState_(self, state):
            self = objc.super(OverlayView, self).initWithFrame_(AppKit.NSMakeRect(0, 0, window_width, window_height))
            if self is None:
                return None
            self._state = state
            return self

        def isOpaque(self):
            return False

        def drawRect_(self, dirty_rect) -> None:
            AppKit.NSColor.clearColor().set()
            AppKit.NSRectFill(dirty_rect)

            snapshot = self._state.snapshot()
            bounds = self.bounds()

            if snapshot.service_enabled:
                AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.2, 1.0, 0.2, 0.95).set()
            else:
                AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.65, 0.65, 0.65, 0.95).set()

            border = AppKit.NSBezierPath.bezierPathWithRect_(bounds)
            border.setLineWidth_(1.0)
            border.stroke()

            if not snapshot.active:
                return

            AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.2, 0.2, 0.95).set()
            for detection in snapshot.detections:
                rect_x, rect_y, rect_width, rect_height = compute_quartz_overlay_rect(
                    detection_bbox=detection.bbox,
                    roi_rect=snapshot.roi_rect,
                    overlay_width=float(bounds.size.width),
                    overlay_height=float(bounds.size.height),
                )
                rect = AppKit.NSMakeRect(rect_x, rect_y, rect_width, rect_height)
                path = AppKit.NSBezierPath.bezierPathWithRect_(rect)
                path.setLineWidth_(1.0)
                path.stroke()

            offset_label = build_detection_offset_label(roi_rect=snapshot.roi_rect, detections=snapshot.detections)
            if offset_label is not None:
                label_attributes = {
                    AppKit.NSFontAttributeName: AppKit.NSFont.monospacedDigitSystemFontOfSize_weight_(13.0, AppKit.NSFontWeightMedium),
                    AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.98),
                }
                label_string = NSString.stringWithString_(offset_label)
                label_size = label_string.sizeWithAttributes_(label_attributes)
                label_padding_x = 8.0
                label_padding_y = 4.0
                label_origin_x = bounds.size.width - label_size.width - 12.0 - label_padding_x
                label_origin_y = bounds.size.height - label_size.height - 12.0 - label_padding_y
                background_rect = AppKit.NSMakeRect(
                    label_origin_x - label_padding_x,
                    label_origin_y - label_padding_y,
                    label_size.width + (label_padding_x * 2.0),
                    label_size.height + (label_padding_y * 2.0),
                )
                AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.58).set()
                background_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(background_rect, 6.0, 6.0)
                background_path.fill()
                label_string.drawAtPoint_withAttributes_(AppKit.NSMakePoint(label_origin_x, label_origin_y), label_attributes)

    class OverlayController(NSObject):
        def initWithView_worker_state_control_(self, view, detection_worker, state, overlay_control):
            self = objc.super(OverlayController, self).init()
            if self is None:
                return None
            self._view = view
            self._worker = detection_worker
            self._state = state
            self._control = overlay_control
            return self

        def tick_(self, _timer) -> None:
            pressed_buttons = int(AppKit.NSEvent.pressedMouseButtons())
            left_down = bool(pressed_buttons & 1)
            right_down = bool(pressed_buttons & 2)
            active = self._control.compute_active(
                right_mouse_down=right_down,
                infer_only_while_right_mouse_down=infer_only_while_right_mouse_down,
            )
            self._worker.set_active(active)
            self._worker.set_cursor_follow_active(left_down)
            self._state.set_service_enabled(self._control.service_enabled)
            self._view.setNeedsDisplay_(True)

        def toggleService(self) -> None:
            service_enabled = self._control.toggle_service()
            self._state.set_service_enabled(service_enabled)
            if not service_enabled:
                self._worker.set_active(False)
                self._state.set_active(False)
                self._state.clear_detections()
            self._view.setNeedsDisplay_(True)

    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

    style_mask = AppKit.NSWindowStyleMaskBorderless
    window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        window_frame,
        style_mask,
        AppKit.NSBackingStoreBuffered,
        False,
    )
    window.setOpaque_(False)
    window.setBackgroundColor_(AppKit.NSColor.clearColor())
    window.setLevel_(AppKit.NSStatusWindowLevel)
    window.setIgnoresMouseEvents_(True)
    window.setReleasedWhenClosed_(False)
    window.setCollectionBehavior_(
        AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
    )

    view = OverlayView.alloc().initWithState_(overlay_state)
    window.setContentView_(view)
    window.orderFrontRegardless()

    controller = OverlayController.alloc().initWithView_worker_state_control_(view, worker, overlay_state, control)
    timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        1.0 / 60.0,
        controller,
        objc.selector(OverlayController.tick_, signature=b"v@:@"),
        None,
        True,
    )

    def _handle_key_event(event) -> None:
        characters = event.charactersIgnoringModifiers()
        if should_toggle_for_characters(characters):
            controller.toggleService()

    key_monitor = AppKit.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        AppKit.NSEventMaskKeyDown,
        _handle_key_event,
    )
    if key_monitor is None:
        raise RuntimeError("Failed to install the global key monitor for the L toggle hotkey")

    print("Overlay hotkey ready: press L to toggle detection service.")

    def _stop_overlay(_signum=None, _frame=None):
        if key_monitor is not None:
            AppKit.NSEvent.removeMonitor_(key_monitor)
        timer.invalidate()
        worker.stop()
        window.orderOut_(None)
        AppHelper.stopEventLoop()

    previous_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, _stop_overlay)

    worker.start()
    try:
        AppHelper.runEventLoop()
    finally:
        signal.signal(signal.SIGINT, previous_handler)
        if key_monitor is not None:
            AppKit.NSEvent.removeMonitor_(key_monitor)
        timer.invalidate()
        worker.stop()
        window.orderOut_(None)

    return 0
