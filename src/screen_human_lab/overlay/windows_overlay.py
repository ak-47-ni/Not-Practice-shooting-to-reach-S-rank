from __future__ import annotations

import signal
import sys
import time
from threading import Event, Lock, Thread

from screen_human_lab.overlay.control import OverlayControl
from screen_human_lab.overlay.state import OverlayState, build_detection_offset_label
from screen_human_lab.pipeline.gated_runtime import GatedDetectionRuntime
from screen_human_lab.roi import RoiRect


WINDOW_REFRESH_HZ = 60.0
VK_RBUTTON = 0x02
VK_L_KEY = 0x4C



def compute_overlay_window_rect(roi_rect: RoiRect) -> tuple[int, int, int, int]:
    return (roi_rect.left, roi_rect.top, roi_rect.width, roi_rect.height)



def compute_overlay_rect(
    detection_bbox: tuple[int, int, int, int],
    roi_rect: RoiRect,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = detection_bbox
    local_x1 = max(0, min(x1 - roi_rect.left, roi_rect.width))
    local_y1 = max(0, min(y1 - roi_rect.top, roi_rect.height))
    local_x2 = max(0, min(x2 - roi_rect.left, roi_rect.width))
    local_y2 = max(0, min(y2 - roi_rect.top, roi_rect.height))
    return (
        int(local_x1),
        int(local_y1),
        max(int(local_x2 - local_x1), 0),
        max(int(local_y2 - local_y1), 0),
    )


class WindowsGatedDetectionWorker:
    def __init__(
        self,
        *,
        runtime: GatedDetectionRuntime,
        target_fps: int,
        initial_active: bool,
    ) -> None:
        self._runtime = runtime
        self._target_fps = max(target_fps, 1)
        self._stop_event = Event()
        self._lock = Lock()
        self._active = initial_active
        self._thread: Thread | None = None
        self._has_cleared = False

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = Thread(target=self._run_loop, name="screen-human-lab-win-overlay", daemon=True)
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

    def _run_loop(self) -> None:
        frame_interval = 1.0 / self._target_fps
        while not self._stop_event.is_set():
            active = self._is_active()
            if not active:
                if not self._has_cleared:
                    self._runtime.process_once(active=False)
                    self._has_cleared = True
                time.sleep(0.01)
                continue

            started = time.perf_counter()
            self._runtime.process_once(active=True)
            self._has_cleared = False
            remaining = frame_interval - (time.perf_counter() - started)
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
    stability_config=None,
) -> int:
    if sys.platform != "win32":
        raise RuntimeError("Windows overlay mode requires Windows")

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    overlay_state = OverlayState(roi_rect=capture.roi_rect)
    control = OverlayControl()
    overlay_state.set_service_enabled(control.service_enabled)
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=tracker_factory,
        stability_config=stability_config,
    )
    worker = WindowsGatedDetectionWorker(
        runtime=runtime,
        target_fps=target_fps,
        initial_active=control.compute_active(
            right_mouse_down=False,
            infer_only_while_right_mouse_down=infer_only_while_right_mouse_down,
        ),
    )

    WNDPROCTYPE = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROCTYPE),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HCURSOR),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("message", wintypes.UINT),
            ("wParam", wintypes.WPARAM),
            ("lParam", wintypes.LPARAM),
            ("time", wintypes.DWORD),
            ("pt", POINT),
            ("lPrivate", wintypes.DWORD),
        ]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    WS_POPUP = 0x80000000
    WS_EX_LAYERED = 0x00080000
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_NOACTIVATE = 0x08000000
    LWA_COLORKEY = 0x00000001
    SW_SHOW = 5
    WM_DESTROY = 0x0002
    WM_CLOSE = 0x0010
    WM_PAINT = 0x000F
    PM_REMOVE = 0x0001
    NULL_BRUSH = 5
    TRANSPARENT = 1

    border_color = (0, 255, 0)
    disabled_border_color = (150, 150, 150)
    detection_color = (255, 80, 80)
    background_color = (0, 0, 0)
    white_color = (255, 255, 255)

    h_instance = kernel32.GetModuleHandleW(None)
    class_name = f"ScreenHumanLabWinOverlay{int(time.time() * 1000)}"
    should_exit = Event()
    state = {"l_key_down": False}

    def rgb(red: int, green: int, blue: int) -> int:
        return red | (green << 8) | (blue << 16)

    def is_key_down(virtual_key: int) -> bool:
        return bool(user32.GetAsyncKeyState(virtual_key) & 0x8000)

    def draw(hwnd) -> None:
        hdc = user32.GetDC(hwnd)
        if not hdc:
            return
        try:
            client_rect = RECT()
            user32.GetClientRect(hwnd, ctypes.byref(client_rect))
            width = client_rect.right - client_rect.left
            height = client_rect.bottom - client_rect.top

            background_brush = gdi32.CreateSolidBrush(rgb(*background_color))
            user32.FillRect(hdc, ctypes.byref(client_rect), background_brush)
            gdi32.DeleteObject(background_brush)

            snapshot = overlay_state.snapshot()
            border_rgb = border_color if snapshot.service_enabled else disabled_border_color
            pen = gdi32.CreatePen(0, 1, rgb(*border_rgb))
            old_pen = gdi32.SelectObject(hdc, pen)
            null_brush = gdi32.GetStockObject(NULL_BRUSH)
            old_brush = gdi32.SelectObject(hdc, null_brush)
            gdi32.Rectangle(hdc, 0, 0, width - 1, height - 1)

            if snapshot.active:
                detection_pen = gdi32.CreatePen(0, 1, rgb(*detection_color))
                gdi32.SelectObject(hdc, detection_pen)
                for detection in snapshot.detections:
                    local_x, local_y, local_width, local_height = compute_overlay_rect(detection.bbox, snapshot.roi_rect)
                    if local_width <= 0 or local_height <= 0:
                        continue
                    gdi32.Rectangle(hdc, local_x, local_y, local_x + local_width, local_y + local_height)
                gdi32.SelectObject(hdc, pen)
                gdi32.DeleteObject(detection_pen)

            gdi32.SelectObject(hdc, old_brush)
            gdi32.SelectObject(hdc, old_pen)
            gdi32.DeleteObject(pen)

            label = build_detection_offset_label(roi_rect=snapshot.roi_rect, detections=snapshot.detections)
            if label is not None:
                gdi32.SetBkMode(hdc, TRANSPARENT)
                gdi32.SetTextColor(hdc, rgb(*white_color))
                gdi32.TextOutW(hdc, max(width - 140, 6), 6, label, len(label))
        finally:
            user32.ReleaseDC(hwnd, hdc)

    def poll_input_and_render(hwnd) -> None:
        right_down = is_key_down(VK_RBUTTON)
        l_down = is_key_down(VK_L_KEY)
        if l_down and not state["l_key_down"]:
            service_enabled = control.toggle_service()
            overlay_state.set_service_enabled(service_enabled)
            if not service_enabled:
                worker.set_active(False)
                overlay_state.set_active(False)
                overlay_state.clear_detections()
        state["l_key_down"] = l_down
        active = control.compute_active(
            right_mouse_down=right_down,
            infer_only_while_right_mouse_down=infer_only_while_right_mouse_down,
        )
        worker.set_active(active)
        overlay_state.set_service_enabled(control.service_enabled)
        draw(hwnd)

    def handle_close(hwnd) -> None:
        if should_exit.is_set():
            return
        should_exit.set()
        worker.stop()
        user32.DestroyWindow(hwnd)

    @WNDPROCTYPE
    def wnd_proc(hwnd, message, w_param, l_param):
        if message == WM_CLOSE:
            handle_close(hwnd)
            return 0
        if message == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        if message == WM_PAINT:
            draw(hwnd)
            return 0
        return user32.DefWindowProcW(hwnd, message, w_param, l_param)

    wnd_class = WNDCLASSW()
    wnd_class.lpfnWndProc = wnd_proc
    wnd_class.hInstance = h_instance
    wnd_class.lpszClassName = class_name
    wnd_class.hbrBackground = gdi32.CreateSolidBrush(rgb(*background_color))
    atom = user32.RegisterClassW(ctypes.byref(wnd_class))
    if atom == 0:
        raise RuntimeError("Failed to register the Windows overlay window class")

    left, top, width, height = compute_overlay_window_rect(capture.roi_rect)
    hwnd = user32.CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        class_name,
        "Screen Human Lab Overlay",
        WS_POPUP,
        left,
        top,
        width,
        height,
        None,
        None,
        h_instance,
        None,
    )
    if not hwnd:
        raise RuntimeError("Failed to create the Windows overlay window")

    user32.SetLayeredWindowAttributes(hwnd, rgb(*background_color), 0, LWA_COLORKEY)
    user32.ShowWindow(hwnd, SW_SHOW)
    user32.UpdateWindow(hwnd)

    previous_handler = signal.getsignal(signal.SIGINT)

    def _stop_overlay(_signum=None, _frame=None):
        should_exit.set()
        try:
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        except Exception:
            pass

    signal.signal(signal.SIGINT, _stop_overlay)
    worker.start()
    print("Windows overlay ready: press and hold right mouse to run detection, press L to toggle service.")
    try:
        msg = MSG()
        last_refresh_at = 0.0
        refresh_interval = 1.0 / WINDOW_REFRESH_HZ
        while not should_exit.is_set():
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            now = time.perf_counter()
            if now - last_refresh_at >= refresh_interval:
                poll_input_and_render(hwnd)
                last_refresh_at = now
            time.sleep(0.004)
    finally:
        signal.signal(signal.SIGINT, previous_handler)
        should_exit.set()
        worker.stop()
        try:
            user32.DestroyWindow(hwnd)
        except Exception:
            pass
        try:
            user32.UnregisterClassW(class_name, h_instance)
        except Exception:
            pass
        gdi32.DeleteObject(wnd_class.hbrBackground)

    return 0
