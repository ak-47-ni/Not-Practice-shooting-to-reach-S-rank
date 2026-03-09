from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from screen_human_lab.capture.base import FrameCapture
from screen_human_lab.inference.base import Detection, InferenceBackend
from screen_human_lab.roi import RoiRect
from screen_human_lab.tracking.template_match import TemplateMatchTracker


DEFAULT_MAX_LOST_FRAMES = 5
TrackerFactory = Callable[[], object]


@dataclass(frozen=True)
class GatedProcessResult:
    detections: list[Detection]
    active: bool
    roi_rect: RoiRect


class GatedDetectionRuntime:
    def __init__(
        self,
        *,
        capture: FrameCapture,
        backend: InferenceBackend,
        overlay_state,
        tracker_factory: TrackerFactory | None = None,
        max_lost_frames: int = DEFAULT_MAX_LOST_FRAMES,
    ) -> None:
        self._capture = capture
        self._backend = backend
        self._overlay_state = overlay_state
        self._overlay_state.set_roi_rect(capture.roi_rect)
        self._tracker = tracker_factory() if tracker_factory is not None else TemplateMatchTracker()
        self._max_lost_frames = max(max_lost_frames, 0)
        self._locked_detection: Detection | None = None
        self._lost_frames = 0

    def _globalize_bbox(self, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        if hasattr(self._capture, "globalize_bbox"):
            return self._capture.globalize_bbox(bbox)
        rect = self._capture.roi_rect
        x1, y1, x2, y2 = bbox
        return (rect.left + x1, rect.top + y1, rect.left + x2, rect.top + y2)

    def _clear_lock(self) -> None:
        clear = getattr(self._tracker, "clear", None)
        if callable(clear):
            clear()
        self._locked_detection = None
        self._lost_frames = 0

    def _select_target(self, detections: list[Detection], frame_shape: tuple[int, ...]) -> Detection | None:
        candidates = [detection for detection in detections if detection.label == "person"] or detections
        if not candidates:
            return None

        center_x = frame_shape[1] / 2.0
        center_y = frame_shape[0] / 2.0
        return min(
            candidates,
            key=lambda detection: _distance_sq_to_center(detection.bbox, center_x=center_x, center_y=center_y),
        )

    def _detect_and_lock(self, frame) -> list[Detection]:
        detections = self._backend.predict(frame)
        selected = self._select_target(detections, frame.shape)
        if selected is None:
            return []

        self._tracker.initialize(frame, selected.bbox)
        self._locked_detection = selected
        self._lost_frames = 0
        return [selected]

    def _track_locked_target(self, frame) -> list[Detection]:
        if self._locked_detection is None:
            return self._detect_and_lock(frame)

        tracking_result = self._tracker.update(frame)
        if tracking_result.success and tracking_result.bbox is not None:
            self._locked_detection = Detection(
                label=self._locked_detection.label,
                confidence=self._locked_detection.confidence,
                bbox=tracking_result.bbox,
            )
            self._lost_frames = 0
            return [self._locked_detection]

        self._lost_frames += 1
        if self._lost_frames <= self._max_lost_frames:
            return [self._locked_detection]

        self._clear_lock()
        return self._detect_and_lock(frame)

    def process_once(self, *, active: bool) -> GatedProcessResult:
        self._overlay_state.set_active(active)
        if not active:
            self._clear_lock()
            self._overlay_state.clear_detections()
            return GatedProcessResult(detections=[], active=False, roi_rect=self._capture.roi_rect)

        frame = self._capture.grab()
        local_detections = self._detect_and_lock(frame) if self._locked_detection is None else self._track_locked_target(frame)
        global_detections = [
            Detection(
                label=detection.label,
                confidence=detection.confidence,
                bbox=self._globalize_bbox(detection.bbox),
            )
            for detection in local_detections
        ]
        self._overlay_state.set_detections(global_detections)
        return GatedProcessResult(detections=global_detections, active=True, roi_rect=self._capture.roi_rect)



def _distance_sq_to_center(
    bbox: tuple[int, int, int, int],
    *,
    center_x: float,
    center_y: float,
) -> float:
    x1, y1, x2, y2 = bbox
    bbox_center_x = (x1 + x2) / 2.0
    bbox_center_y = (y1 + y2) / 2.0
    delta_x = bbox_center_x - center_x
    delta_y = bbox_center_y - center_y
    return (delta_x * delta_x) + (delta_y * delta_y)
