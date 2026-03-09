from screen_human_lab.roi import RoiRect, compute_center_square_roi


def test_compute_center_square_roi_uses_requested_size_when_monitor_can_fit() -> None:
    roi = compute_center_square_roi({"left": 100, "top": 50, "width": 1600, "height": 1200}, 1000)

    assert roi == RoiRect(left=400, top=150, width=1000, height=1000)


def test_compute_center_square_roi_falls_back_to_monitor_height() -> None:
    roi = compute_center_square_roi({"left": 0, "top": 0, "width": 1470, "height": 956}, 1000)

    assert roi == RoiRect(left=257, top=0, width=956, height=956)
