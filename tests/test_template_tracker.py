import numpy as np

from screen_human_lab.tracking.template_match import TemplateMatchTracker


PATCH_SIZE = 20


def _make_patch() -> np.ndarray:
    patch = np.zeros((PATCH_SIZE, PATCH_SIZE, 3), dtype=np.uint8)
    patch[..., 0] = np.tile(np.arange(PATCH_SIZE, dtype=np.uint8) * 8, (PATCH_SIZE, 1))
    patch[..., 1] = np.tile((np.arange(PATCH_SIZE, dtype=np.uint8) * 8).reshape(PATCH_SIZE, 1), (1, PATCH_SIZE))
    patch[..., 2] = 180
    return patch


PATCH = _make_patch()


def _make_frame(*, x: int, y: int, width: int = 96, height: int = 96) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[y : y + PATCH_SIZE, x : x + PATCH_SIZE] = PATCH
    return frame


def test_template_tracker_updates_bbox_for_translated_patch() -> None:
    tracker = TemplateMatchTracker()
    tracker.initialize(_make_frame(x=20, y=20), (20, 20, 40, 40))

    result = tracker.update(_make_frame(x=26, y=24))

    assert result.success is True
    assert result.bbox == (26, 24, 46, 44)


def test_template_tracker_reports_failure_when_patch_disappears() -> None:
    tracker = TemplateMatchTracker(match_threshold=0.8)
    tracker.initialize(_make_frame(x=20, y=20), (20, 20, 40, 40))

    result = tracker.update(np.zeros((96, 96, 3), dtype=np.uint8))

    assert result.success is False
    assert result.bbox is None



def test_template_tracker_uses_motion_prediction_for_faster_second_move() -> None:
    tracker = TemplateMatchTracker(
        match_threshold=0.45,
        search_padding=4,
        max_search_padding=24,
        prediction_gain=1.0,
    )
    tracker.initialize(_make_frame(x=20, y=20), (20, 20, 40, 40))

    first = tracker.update(_make_frame(x=26, y=24))
    second = tracker.update(_make_frame(x=38, y=30))

    assert first.success is True
    assert second.success is True
    assert second.bbox == (38, 30, 58, 50)
