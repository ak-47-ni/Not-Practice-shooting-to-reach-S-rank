from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from screen_human_lab.capture.base import FrameCapture
from screen_human_lab.config import StabilityConfig
from screen_human_lab.inference.base import Detection, InferenceBackend
from screen_human_lab.pipeline.global_motion import GlobalMotionEstimator, MotionEstimate
from screen_human_lab.pipeline.lock_state import LockStateMachine
from screen_human_lab.pipeline.target_filter import TargetStateFilter
from screen_human_lab.pipeline.target_scoring import ScoringWeights, select_best_detection
from screen_human_lab.roi import RoiRect
from screen_human_lab.tracking.template_match import TemplateMatchTracker


DEFAULT_MAX_LOST_FRAMES = 5
TrackerFactory = Callable[[], object]


@dataclass(frozen=True)
class GatedProcessResult:
    detections: list[Detection]
    active: bool
    roi_rect: RoiRect
    frame: np.ndarray | None = None
    state: str = "idle"
    motion: MotionEstimate = field(default_factory=MotionEstimate)


class GatedDetectionRuntime:
    def __init__(
        self,
        *,
        capture: FrameCapture,
        backend: InferenceBackend,
        overlay_state,
        tracker_factory: TrackerFactory | None = None,
        max_lost_frames: int = DEFAULT_MAX_LOST_FRAMES,
        stability_config: StabilityConfig | None = None,
        globalize_output: bool = True,
    ) -> None:
        self._capture = capture
        self._backend = backend
        self._overlay_state = overlay_state
        self._overlay_state.set_roi_rect(capture.roi_rect)
        self._tracker = tracker_factory() if tracker_factory is not None else TemplateMatchTracker()
        if stability_config is None:
            stability_config = StabilityConfig(max_lost_frames=max_lost_frames)
        self._stability = stability_config
        self._globalize_output = globalize_output
        self._motion_estimator = GlobalMotionEstimator()
        self._scoring_weights = ScoringWeights(
            confidence_weight=self._stability.confidence_weight,
            iou_weight=self._stability.iou_weight,
            distance_weight=self._stability.distance_weight,
            size_weight=self._stability.size_weight,
        )
        self._lock_state = LockStateMachine(max_lost_frames=self._stability.max_lost_frames)
        self._target_filter = TargetStateFilter(smoothing_factor=self._stability.smoothing_factor)
        self._locked_detection: Detection | None = None
        self._previous_frame: np.ndarray | None = None

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
        self._lock_state.clear()
        self._target_filter.reset()

    def _select_target(
        self,
        detections: list[Detection],
        frame_shape: tuple[int, ...],
        *,
        predicted_bbox: tuple[int, int, int, int] | None = None,
    ) -> Detection | None:
        candidates = [detection for detection in detections if detection.label == "person"] or detections
        if not candidates:
            return None
        return select_best_detection(
            candidates,
            frame_shape=frame_shape,
            predicted_bbox=predicted_bbox,
            weights=self._scoring_weights,
        )

    def _detect_and_lock(
        self,
        frame: np.ndarray,
        *,
        predicted_bbox: tuple[int, int, int, int] | None = None,
    ) -> list[Detection]:
        self._lock_state.begin_acquiring()
        detections = self._backend.predict(frame)
        selected = self._select_target(detections, frame.shape, predicted_bbox=predicted_bbox)
        if selected is None:
            return []

        self._tracker.initialize(frame, selected.bbox)
        self._locked_detection = selected
        self._lock_state.lock_acquired()
        return [selected]

    def _predicted_bbox(self, motion: MotionEstimate) -> tuple[int, int, int, int] | None:
        if self._locked_detection is None:
            return None
        x1, y1, x2, y2 = self._locked_detection.bbox
        shift_x = int(round(motion.delta_x))
        shift_y = int(round(motion.delta_y))
        return (x1 + shift_x, y1 + shift_y, x2 + shift_x, y2 + shift_y)

    def _track_locked_target(self, frame: np.ndarray, *, motion: MotionEstimate) -> list[Detection]:
        if self._locked_detection is None:
            return self._detect_and_lock(frame)

        predicted_bbox = self._predicted_bbox(motion)
        tracking_result = self._tracker.update(frame, motion_hint=(motion.delta_x, motion.delta_y))
        if tracking_result.success and tracking_result.bbox is not None:
            self._locked_detection = Detection(
                label=self._locked_detection.label,
                confidence=self._locked_detection.confidence,
                bbox=tracking_result.bbox,
            )
            self._lock_state.lock_acquired()
            return [self._locked_detection]

        if self._lock_state.mark_lost() and self._locked_detection is not None:
            return [self._locked_detection]

        redetected = self._detect_and_lock(frame, predicted_bbox=predicted_bbox)
        if redetected:
            return redetected

        self._clear_lock()
        return []

    def _stabilize_detections(self, detections: list[Detection]) -> list[Detection]:
        if not detections or not self._stability.enabled or self._globalize_output:
            return detections
        primary = detections[0]
        stabilized_bbox = self._target_filter.update(primary.bbox)
        return [Detection(label=primary.label, confidence=primary.confidence, bbox=stabilized_bbox)]

    def _format_output_detections(self, detections: list[Detection]) -> list[Detection]:
        if not self._globalize_output:
            return detections
        return [
            Detection(
                label=detection.label,
                confidence=detection.confidence,
                bbox=self._globalize_bbox(detection.bbox),
            )
            for detection in detections
        ]

    def process_once(self, *, active: bool) -> GatedProcessResult:
        self._overlay_state.set_active(active)
        if not active:
            self._clear_lock()
            self._overlay_state.clear_detections()
            self._previous_frame = None
            return GatedProcessResult(detections=[], active=False, roi_rect=self._capture.roi_rect)

        frame = self._capture.grab()
        if self._stability.enabled and self._stability.enable_global_motion:
            motion = self._motion_estimator.estimate(self._previous_frame, frame)
        else:
            motion = MotionEstimate()
        self._previous_frame = frame

        local_detections = self._detect_and_lock(frame) if self._locked_detection is None else self._track_locked_target(frame, motion=motion)
        stabilized_detections = self._stabilize_detections(local_detections)
        output_detections = self._format_output_detections(stabilized_detections)
        self._overlay_state.set_detections(output_detections)
        return GatedProcessResult(
            detections=output_detections,
            active=True,
            roi_rect=self._capture.roi_rect,
            frame=frame,
            state=self._lock_state.status.value,
            motion=motion,
        )
