import numpy as np

from screen_human_lab.pipeline.global_motion import GlobalMotionEstimator


PATCH_SIZE = 20


def _make_patch() -> np.ndarray:
    patch = np.zeros((PATCH_SIZE, PATCH_SIZE, 3), dtype=np.uint8)
    patch[..., 0] = np.tile(np.arange(PATCH_SIZE, dtype=np.uint8) * 8, (PATCH_SIZE, 1))
    patch[..., 1] = np.tile((np.arange(PATCH_SIZE, dtype=np.uint8) * 8).reshape(PATCH_SIZE, 1), (1, PATCH_SIZE))
    patch[..., 2] = 180
    return patch


def _make_frame(*, x: int, y: int, width: int = 96, height: int = 96) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[y : y + PATCH_SIZE, x : x + PATCH_SIZE] = _make_patch()
    return frame


def test_global_motion_estimator_returns_zero_without_previous_frame() -> None:
    estimator = GlobalMotionEstimator()

    result = estimator.estimate(None, _make_frame(x=20, y=20))

    assert result.delta_x == 0.0
    assert result.delta_y == 0.0
    assert result.confidence == 0.0


def test_global_motion_estimator_detects_frame_translation() -> None:
    estimator = GlobalMotionEstimator()

    result = estimator.estimate(_make_frame(x=20, y=20), _make_frame(x=26, y=24))

    assert abs(result.delta_x - 6.0) < 1.0
    assert abs(result.delta_y - 4.0) < 1.0
    assert result.confidence >= 0.0
