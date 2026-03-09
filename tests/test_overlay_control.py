from screen_human_lab.inference.base import Detection
from screen_human_lab.overlay.appkit_overlay import (
    compute_quartz_cursor_position,
    compute_quartz_overlay_rect,
    compute_quartz_screen_rect,
    compute_quartz_target_point,
    load_core_graphics_mouse_warp,
)
from screen_human_lab.overlay.control import CursorFollowController, OverlayControl, should_toggle_for_characters
from screen_human_lab.roi import RoiRect


def test_service_toggle_flips_enabled_state() -> None:
    control = OverlayControl()

    assert control.service_enabled is True

    control.toggle_service()

    assert control.service_enabled is False


def test_compute_active_requires_service_enabled_and_right_mouse_gate() -> None:
    control = OverlayControl(service_enabled=False)

    assert control.compute_active(right_mouse_down=True, infer_only_while_right_mouse_down=True) is False

    control.toggle_service()

    assert control.compute_active(right_mouse_down=False, infer_only_while_right_mouse_down=True) is False
    assert control.compute_active(right_mouse_down=True, infer_only_while_right_mouse_down=True) is True


def test_compute_active_ignores_right_mouse_gate_when_disabled_in_config() -> None:
    control = OverlayControl(service_enabled=True)

    assert control.compute_active(right_mouse_down=False, infer_only_while_right_mouse_down=False) is True


def test_should_toggle_for_characters_matches_l_case_insensitively() -> None:
    assert should_toggle_for_characters("l") is True
    assert should_toggle_for_characters("L") is True
    assert should_toggle_for_characters("k") is False
    assert should_toggle_for_characters(None) is False


class _FakeCursorMover:
    def __init__(self) -> None:
        self.moves: list[tuple[float, float]] = []

    def move_to(self, target_x: float, target_y: float) -> None:
        self.moves.append((target_x, target_y))


def test_cursor_follow_controller_moves_from_current_cursor_toward_target_center() -> None:
    mover = _FakeCursorMover()
    controller = CursorFollowController(
        mover=mover,
        cursor_position_provider=lambda: (400.0, 300.0),
        fallback_position_provider=lambda roi_rect: (600.0, 700.0),
        target_position_provider=lambda detection, roi_rect: (460.0, 380.0),
        speed_pixels_per_second=50.0,
        min_distance=0.0,
    )

    moved = controller.update(
        active=True,
        roi_rect=RoiRect(left=100, top=200, width=1000, height=1000),
        detections=[Detection(label="person", confidence=0.9, bbox=(650, 850, 750, 950))],
        delta_time=1.0,
    )

    assert moved is True
    assert mover.moves == [(430.0, 340.0)]


def test_cursor_follow_controller_skips_when_inactive_or_missing_detection() -> None:
    mover = _FakeCursorMover()
    controller = CursorFollowController(
        mover=mover,
        cursor_position_provider=lambda: (400.0, 300.0),
        fallback_position_provider=lambda roi_rect: (600.0, 700.0),
        target_position_provider=lambda detection, roi_rect: (460.0, 380.0),
        speed_pixels_per_second=50.0,
        min_distance=0.0,
    )
    roi_rect = RoiRect(left=100, top=200, width=1000, height=1000)

    inactive = controller.update(
        active=False,
        roi_rect=roi_rect,
        detections=[Detection(label="person", confidence=0.9, bbox=(650, 850, 750, 950))],
        delta_time=1.0,
    )
    missing = controller.update(active=True, roi_rect=roi_rect, detections=[], delta_time=1.0)

    assert inactive is False
    assert missing is False
    assert mover.moves == []


def test_cursor_follow_controller_falls_back_to_roi_center_when_cursor_position_is_unavailable() -> None:
    mover = _FakeCursorMover()
    controller = CursorFollowController(
        mover=mover,
        cursor_position_provider=lambda: (_ for _ in ()).throw(RuntimeError("mouse unavailable")),
        fallback_position_provider=lambda roi_rect: (600.0, 700.0),
        target_position_provider=lambda detection, roi_rect: (660.0, 780.0),
        speed_pixels_per_second=50.0,
        min_distance=0.0,
    )

    moved = controller.update(
        active=True,
        roi_rect=RoiRect(left=100, top=200, width=1000, height=1000),
        detections=[Detection(label="person", confidence=0.9, bbox=(650, 850, 750, 950))],
        delta_time=1.0,
    )

    assert moved is True
    assert mover.moves == [(630.0, 740.0)]


def test_cursor_follow_controller_reuses_last_moved_position_when_cursor_readback_fails() -> None:
    mover = _FakeCursorMover()
    positions = iter([(100.0, 100.0), RuntimeError("mouse unavailable")])

    def _cursor_position_provider() -> tuple[float, float]:
        value = next(positions)
        if isinstance(value, Exception):
            raise value
        return value

    controller = CursorFollowController(
        mover=mover,
        cursor_position_provider=_cursor_position_provider,
        fallback_position_provider=lambda roi_rect: (0.0, 0.0),
        target_position_provider=lambda detection, roi_rect: (200.0, 100.0),
        speed_pixels_per_second=100.0,
        min_distance=0.0,
    )
    roi_rect = RoiRect(left=100, top=200, width=1000, height=1000)

    first_moved = controller.update(
        active=True,
        roi_rect=roi_rect,
        detections=[Detection(label="person", confidence=0.9, bbox=(650, 850, 750, 950))],
        delta_time=0.5,
    )
    second_moved = controller.update(
        active=True,
        roi_rect=roi_rect,
        detections=[Detection(label="person", confidence=0.9, bbox=(650, 850, 750, 950))],
        delta_time=0.5,
    )

    assert first_moved is True
    assert second_moved is True
    assert mover.moves == [(150.0, 100.0), (200.0, 100.0)]


def test_compute_quartz_cursor_position_adds_quartz_axis_deltas() -> None:
    next_x, next_y = compute_quartz_cursor_position(current_x=400.0, current_y=300.0, step_x=25, step_y=50)

    assert next_x == 425.0
    assert next_y == 350.0


def test_compute_quartz_target_point_converts_screen_style_bbox_center() -> None:
    target_x, target_y = compute_quartz_target_point(
        detection_bbox=(650, 850, 750, 950),
        monitor_left=100,
        monitor_top=200,
        monitor_width=1000,
        monitor_height=1000,
        screen_origin_x=300.0,
        screen_origin_y=50.0,
        screen_width=1000.0,
        screen_height=1000.0,
    )

    assert target_x == 900.0
    assert target_y == 350.0


def test_compute_quartz_target_point_scales_monitor_pixels_into_screen_points() -> None:
    target_x, target_y = compute_quartz_target_point(
        detection_bbox=(900, 400, 1100, 600),
        monitor_left=0,
        monitor_top=0,
        monitor_width=2000,
        monitor_height=1000,
        screen_origin_x=300.0,
        screen_origin_y=50.0,
        screen_width=1000.0,
        screen_height=500.0,
    )

    assert target_x == 800.0
    assert target_y == 300.0


def test_compute_quartz_screen_rect_scales_roi_pixels_into_screen_points() -> None:
    rect_x, rect_y, rect_width, rect_height = compute_quartz_screen_rect(
        rect_left=500,
        rect_top=200,
        rect_width=500,
        rect_height=500,
        monitor_left=0,
        monitor_top=0,
        monitor_width=2000,
        monitor_height=1000,
        screen_origin_x=300.0,
        screen_origin_y=50.0,
        screen_width=1000.0,
        screen_height=500.0,
    )

    assert rect_x == 550.0
    assert rect_y == 200.0
    assert rect_width == 250.0
    assert rect_height == 250.0


def test_compute_quartz_overlay_rect_scales_detection_box_into_overlay_points() -> None:
    rect_x, rect_y, rect_width, rect_height = compute_quartz_overlay_rect(
        detection_bbox=(650, 850, 750, 950),
        roi_rect=RoiRect(left=500, top=500, width=500, height=500),
        overlay_width=250.0,
        overlay_height=250.0,
    )

    assert rect_x == 75.0
    assert rect_y == 25.0
    assert rect_width == 50.0
    assert rect_height == 50.0


class _FakeObjc:
    def __init__(self) -> None:
        self.bundle_calls: list[tuple[str, str, str]] = []
        self.function_calls: list[tuple[object, tuple[tuple[str, bytes], ...]]] = []

    def pathForFramework(self, path: str) -> str:
        return path

    def loadBundle(self, name: str, namespace, *, bundle_path: str):
        self.bundle_calls.append((name, bundle_path, type(namespace).__name__))
        return object()

    def loadBundleFunctions(self, bundle, namespace, functions) -> None:
        self.function_calls.append((bundle, tuple(functions)))
        namespace["CGWarpMouseCursorPosition"] = lambda point: point


def test_load_core_graphics_mouse_warp_uses_application_services_bundle() -> None:
    objc_module = _FakeObjc()

    warp = load_core_graphics_mouse_warp(objc_module)

    assert callable(warp)
    assert objc_module.bundle_calls == [("CoreGraphics", "/System/Library/Frameworks/ApplicationServices.framework", "dict")]
    assert objc_module.function_calls[0][1] == (("CGWarpMouseCursorPosition", b"i{CGPoint=dd}"),)
