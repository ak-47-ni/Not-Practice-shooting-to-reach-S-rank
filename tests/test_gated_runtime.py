from dataclasses import dataclass

import numpy as np

from screen_human_lab.inference.base import Detection
from screen_human_lab.pipeline.gated_runtime import GatedDetectionRuntime
from screen_human_lab.roi import RoiRect
from screen_human_lab.tracking.template_match import TrackingResult


class _FakeCapture:
    roi_rect = RoiRect(left=100, top=200, width=256, height=256)

    def __init__(self, frames: list[np.ndarray] | None = None) -> None:
        self.calls = 0
        self._frames = list(frames) if frames is not None else [np.zeros((256, 256, 3), dtype=np.uint8)]

    def grab(self) -> np.ndarray:
        self.calls += 1
        if len(self._frames) > 1:
            return self._frames.pop(0)
        return self._frames[0]


class _FakeBackend:
    def __init__(self, predictions: list[list[Detection]]) -> None:
        self.calls = 0
        self._predictions = list(predictions)

    def predict(self, frame: np.ndarray) -> list[Detection]:
        self.calls += 1
        if self._predictions:
            return self._predictions.pop(0)
        return []


class _FakeOverlayState:
    def __init__(self) -> None:
        self.active = False
        self.detections = []
        self.roi_rect = None

    def set_roi_rect(self, roi_rect: RoiRect) -> None:
        self.roi_rect = roi_rect

    def set_active(self, active: bool) -> None:
        self.active = active

    def set_detections(self, detections) -> None:
        self.detections = detections

    def clear_detections(self) -> None:
        self.detections = []


@dataclass
class _FakeTracker:
    updates: list[TrackingResult]

    def __post_init__(self) -> None:
        self.initialize_calls: list[tuple[int, int, int, int]] = []
        self.update_calls = 0
        self.clear_calls = 0

    def initialize(self, frame: np.ndarray, bbox: tuple[int, int, int, int]) -> None:
        self.initialize_calls.append(bbox)

    def update(self, frame: np.ndarray) -> TrackingResult:
        self.update_calls += 1
        if self.updates:
            return self.updates.pop(0)
        return TrackingResult(success=False, bbox=None, score=0.0)

    def clear(self) -> None:
        self.clear_calls += 1


class _FakeTrackerFactory:
    def __init__(self, tracker: _FakeTracker) -> None:
        self.tracker = tracker

    def __call__(self):
        return self.tracker


def test_gated_service_skips_inference_when_left_mouse_not_pressed() -> None:
    capture = _FakeCapture()
    backend = _FakeBackend(predictions=[])
    overlay_state = _FakeOverlayState()
    tracker = _FakeTracker([])
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=_FakeTrackerFactory(tracker),
    )

    result = runtime.process_once(active=False)

    assert result.detections == []
    assert capture.calls == 0
    assert backend.calls == 0
    assert overlay_state.active is False


def test_runtime_selects_single_target_closest_to_roi_center() -> None:
    capture = _FakeCapture()
    backend = _FakeBackend(
        predictions=[
            [
                Detection(label="person", confidence=0.7, bbox=(0, 0, 40, 40)),
                Detection(label="person", confidence=0.9, bbox=(100, 100, 140, 140)),
            ]
        ]
    )
    overlay_state = _FakeOverlayState()
    tracker = _FakeTracker([])
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=_FakeTrackerFactory(tracker),
    )

    result = runtime.process_once(active=True)

    assert backend.calls == 1
    assert len(result.detections) == 1
    assert result.detections[0].bbox == (200, 300, 240, 340)
    assert tracker.initialize_calls == [(100, 100, 140, 140)]
    assert overlay_state.detections[0].bbox == (200, 300, 240, 340)


def test_runtime_uses_tracker_updates_while_locked() -> None:
    capture = _FakeCapture(frames=[np.zeros((256, 256, 3), dtype=np.uint8), np.zeros((256, 256, 3), dtype=np.uint8)])
    backend = _FakeBackend(predictions=[[Detection(label="person", confidence=0.9, bbox=(10, 20, 30, 40))]])
    overlay_state = _FakeOverlayState()
    tracker = _FakeTracker([TrackingResult(success=True, bbox=(12, 24, 32, 44), score=0.92)])
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=_FakeTrackerFactory(tracker),
    )

    first = runtime.process_once(active=True)
    second = runtime.process_once(active=True)

    assert first.detections[0].bbox == (110, 220, 130, 240)
    assert second.detections[0].bbox == (112, 224, 132, 244)
    assert backend.calls == 1
    assert tracker.update_calls == 1


def test_runtime_keeps_last_locked_box_for_five_lost_frames() -> None:
    capture = _FakeCapture(frames=[np.zeros((256, 256, 3), dtype=np.uint8)] * 6)
    backend = _FakeBackend(predictions=[[Detection(label="person", confidence=0.9, bbox=(10, 20, 30, 40))]])
    overlay_state = _FakeOverlayState()
    tracker = _FakeTracker([TrackingResult(success=False, bbox=None, score=0.0) for _ in range(5)])
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=_FakeTrackerFactory(tracker),
    )

    runtime.process_once(active=True)
    results = [runtime.process_once(active=True) for _ in range(5)]

    assert all(result.detections[0].bbox == (110, 220, 130, 240) for result in results)
    assert backend.calls == 1
    assert tracker.update_calls == 5


def test_runtime_redetects_after_sixth_lost_frame() -> None:
    capture = _FakeCapture(frames=[np.zeros((256, 256, 3), dtype=np.uint8)] * 7)
    backend = _FakeBackend(
        predictions=[
            [Detection(label="person", confidence=0.9, bbox=(10, 20, 30, 40))],
            [Detection(label="person", confidence=0.8, bbox=(50, 60, 80, 100))],
        ]
    )
    overlay_state = _FakeOverlayState()
    tracker = _FakeTracker([TrackingResult(success=False, bbox=None, score=0.0) for _ in range(6)])
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=_FakeTrackerFactory(tracker),
    )

    runtime.process_once(active=True)
    for _ in range(5):
        runtime.process_once(active=True)
    result = runtime.process_once(active=True)

    assert backend.calls == 2
    assert tracker.initialize_calls == [(10, 20, 30, 40), (50, 60, 80, 100)]
    assert result.detections[0].bbox == (150, 260, 180, 300)


def test_gated_service_clears_lock_when_becoming_inactive() -> None:
    capture = _FakeCapture(frames=[np.zeros((256, 256, 3), dtype=np.uint8)] * 3)
    backend = _FakeBackend(
        predictions=[
            [Detection(label="person", confidence=0.9, bbox=(10, 20, 30, 40))],
            [Detection(label="person", confidence=0.8, bbox=(50, 60, 80, 100))],
        ]
    )
    overlay_state = _FakeOverlayState()
    tracker = _FakeTracker([])
    runtime = GatedDetectionRuntime(
        capture=capture,
        backend=backend,
        overlay_state=overlay_state,
        tracker_factory=_FakeTrackerFactory(tracker),
    )

    runtime.process_once(active=True)
    inactive = runtime.process_once(active=False)
    resumed = runtime.process_once(active=True)

    assert inactive.detections == []
    assert tracker.clear_calls >= 1
    assert backend.calls == 2
    assert resumed.detections[0].bbox == (150, 260, 180, 300)
