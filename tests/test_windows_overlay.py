from screen_human_lab.overlay.windows_overlay import compute_overlay_rect, compute_overlay_window_rect
from screen_human_lab.roi import RoiRect


def test_compute_overlay_window_rect_matches_roi_bounds() -> None:
    roi_rect = RoiRect(left=100, top=200, width=500, height=500)

    assert compute_overlay_window_rect(roi_rect) == (100, 200, 500, 500)


def test_compute_overlay_rect_projects_global_bbox_into_roi_space() -> None:
    roi_rect = RoiRect(left=100, top=200, width=500, height=500)

    result = compute_overlay_rect((150, 250, 210, 330), roi_rect)

    assert result == (50, 50, 60, 80)


def test_compute_overlay_rect_clips_bbox_to_roi() -> None:
    roi_rect = RoiRect(left=100, top=200, width=500, height=500)

    result = compute_overlay_rect((80, 180, 140, 240), roi_rect)

    assert result == (0, 0, 40, 40)
