import numpy as np

from screen_human_lab.inference.base import Detection
from screen_human_lab.pipeline.runtime import StablePreviewSession
from screen_human_lab.roi import RoiRect


class _FakeCapture:
    roi_rect = RoiRect(left=100, top=200, width=256, height=256)

    def __init__(self) -> None:
        self.frames_grabbed = 0

    def grab(self) -> np.ndarray:
        self.frames_grabbed += 1
        return np.zeros((64, 64, 3), dtype=np.uint8)

    def globalize_bbox(self, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = bbox
        return (x1 + 100, y1 + 200, x2 + 100, y2 + 200)

    def close(self) -> None:
        return None


class _FakeBackend:
    name = "fake-backend"
    device = "cpu"

    def predict(self, frame: np.ndarray) -> list[Detection]:
        return [Detection(label="person", confidence=0.95, bbox=(10, 20, 30, 40))]


def test_stable_preview_session_returns_local_detections() -> None:
    session = StablePreviewSession(capture=_FakeCapture(), backend=_FakeBackend())

    result = session.process_once()

    assert result.frame_index == 1
    assert result.detections[0].bbox == (10, 20, 30, 40)
    assert result.rendered_frame.shape == (64, 64, 3)
