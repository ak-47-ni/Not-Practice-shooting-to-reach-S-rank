import numpy as np

from screen_human_lab.inference.base import Detection
from screen_human_lab.pipeline.runtime import RuntimeSession


class _FakeCapture:
    def __init__(self) -> None:
        self.frames_grabbed = 0

    def grab(self) -> np.ndarray:
        self.frames_grabbed += 1
        return np.zeros((32, 32, 3), dtype=np.uint8)

    def close(self) -> None:
        return None


class _FakeBackend:
    name = "fake-backend"
    device = "cpu"

    def predict(self, frame: np.ndarray) -> list[Detection]:
        return [Detection(label="person", confidence=0.95, bbox=(2, 2, 12, 12))]


def _passthrough_overlay(
    frame: np.ndarray,
    detections: list[Detection],
    summary: dict[str, float],
    *,
    backend_name: str,
    frame_index: int,
) -> np.ndarray:
    assert detections
    assert summary["total_ms"] >= 0.0
    assert backend_name == "fake-backend"
    assert frame_index == 1
    return frame.copy()


def test_runtime_processes_single_frame_with_fake_backend() -> None:
    session = RuntimeSession(
        capture=_FakeCapture(),
        backend=_FakeBackend(),
        overlay_renderer=_passthrough_overlay,
        enable_overlay=True,
    )

    result = session.process_once()

    assert result.frame_index == 1
    assert len(result.detections) == 1
    assert result.rendered_frame.shape == (32, 32, 3)
    assert result.metrics["fps"] >= 0.0


def test_runtime_can_disable_overlay() -> None:
    session = RuntimeSession(
        capture=_FakeCapture(),
        backend=_FakeBackend(),
        overlay_renderer=_passthrough_overlay,
        enable_overlay=False,
    )

    result = session.process_once()

    assert result.rendered_frame.shape == (32, 32, 3)
    assert len(result.detections) == 1
