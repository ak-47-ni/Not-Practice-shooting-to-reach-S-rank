from screen_human_lab.inference.base import Detection
from screen_human_lab.overlay.state import (
    OverlaySnapshot,
    OverlayState,
    build_detection_offset_label,
    compute_cursor_step,
    compute_detection_offset,
    format_detection_offset,
)
from screen_human_lab.roi import RoiRect



def test_overlay_state_clears_boxes_on_release() -> None:
    state = OverlayState(roi_rect=RoiRect(left=10, top=20, width=100, height=100))
    state.set_service_enabled(True)
    state.set_active(True)
    state.set_detections([Detection(label="person", confidence=0.9, bbox=(1, 2, 3, 4))])

    state.clear_detections()
    state.set_active(False)
    snapshot = state.snapshot()

    assert snapshot == OverlaySnapshot(
        roi_rect=RoiRect(left=10, top=20, width=100, height=100),
        detections=[],
        active=False,
        service_enabled=True,
    )



def test_overlay_state_tracks_service_enabled_status() -> None:
    state = OverlayState(roi_rect=RoiRect(left=0, top=0, width=64, height=64))

    assert state.snapshot().service_enabled is True

    state.set_service_enabled(False)

    assert state.snapshot().service_enabled is False



def test_compute_detection_offset_uses_screen_coordinate_signs() -> None:
    roi_rect = RoiRect(left=100, top=200, width=1000, height=1000)
    detection = Detection(label="person", confidence=0.9, bbox=(650, 650, 750, 750))

    offset = compute_detection_offset(roi_rect=roi_rect, detection=detection)

    assert offset.dx == 100
    assert offset.dy == 0


def test_format_detection_offset_keeps_explicit_signs() -> None:
    roi_rect = RoiRect(left=100, top=200, width=1000, height=1000)
    detection = Detection(label="person", confidence=0.9, bbox=(300, 850, 400, 950))

    formatted = format_detection_offset(compute_detection_offset(roi_rect=roi_rect, detection=detection))

    assert formatted == "dx=-250  dy=+200"



def test_build_detection_offset_label_returns_none_when_no_detections() -> None:
    roi_rect = RoiRect(left=0, top=0, width=1000, height=1000)

    assert build_detection_offset_label(roi_rect=roi_rect, detections=[]) is None


def test_compute_cursor_step_moves_along_straight_line_toward_target() -> None:
    step_x, step_y = compute_cursor_step(
        delta_x=60.0,
        delta_y=80.0,
        speed_pixels_per_second=50.0,
        delta_time=1.0,
        min_distance=0.0,
    )

    assert step_x == 30
    assert step_y == 40


def test_compute_cursor_step_snaps_to_target_when_speed_reaches_remaining_distance() -> None:
    step_x, step_y = compute_cursor_step(
        delta_x=30.0,
        delta_y=40.0,
        speed_pixels_per_second=100.0,
        delta_time=1.0,
        min_distance=0.0,
    )

    assert step_x == 30
    assert step_y == 40


def test_compute_cursor_step_stops_within_min_distance() -> None:
    step_x, step_y = compute_cursor_step(
        delta_x=0.6,
        delta_y=0.8,
        speed_pixels_per_second=100.0,
        delta_time=1.0,
        min_distance=1.1,
    )

    assert step_x == 0.0
    assert step_y == 0.0
