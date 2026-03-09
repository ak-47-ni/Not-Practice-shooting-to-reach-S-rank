from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

import numpy as np

from screen_human_lab.capture.base import FrameCapture
from screen_human_lab.inference.base import Detection, InferenceBackend
from screen_human_lab.pipeline.metrics import RollingMetrics, TimingSample
from screen_human_lab.pipeline.overlay import render_overlay


OverlayRenderer = Callable[[np.ndarray, list[Detection], dict[str, float]], np.ndarray]


@dataclass(frozen=True)
class ProcessedFrame:
    frame_index: int
    detections: list[Detection]
    rendered_frame: np.ndarray
    metrics: dict[str, float]


class RuntimeSession:
    def __init__(
        self,
        *,
        capture: FrameCapture,
        backend: InferenceBackend,
        overlay_renderer: Callable[..., np.ndarray] = render_overlay,
        enable_overlay: bool = True,
        metrics: RollingMetrics | None = None,
    ) -> None:
        self._capture = capture
        self._backend = backend
        self._overlay_renderer = overlay_renderer
        self._enable_overlay = enable_overlay
        self._metrics = metrics or RollingMetrics()
        self._frame_index = 0

    def process_once(self) -> ProcessedFrame:
        loop_started = perf_counter()

        frame = self._capture.grab()
        after_capture = perf_counter()

        detections = self._backend.predict(frame)
        after_inference = perf_counter()

        summary_before_overlay = self._metrics.summary()
        if self._enable_overlay:
            rendered_frame = self._overlay_renderer(
                frame,
                detections,
                summary_before_overlay,
                backend_name=self._backend.name,
                frame_index=self._frame_index + 1,
            )
        else:
            rendered_frame = frame.copy()
        after_overlay = perf_counter()

        sample = TimingSample(
            capture_ms=(after_capture - loop_started) * 1000.0,
            inference_ms=(after_inference - after_capture) * 1000.0,
            overlay_ms=(after_overlay - after_inference) * 1000.0,
            total_ms=(after_overlay - loop_started) * 1000.0,
        )
        self._metrics.add(sample)
        self._frame_index += 1

        return ProcessedFrame(
            frame_index=self._frame_index,
            detections=detections,
            rendered_frame=rendered_frame,
            metrics=self._metrics.summary(),
        )

    def run(self, *, max_frames: int | None = None, show_window: bool = True, window_name: str = "Screen Human Lab") -> int:
        processed_frames = 0
        cv2 = None
        if show_window:
            try:
                import cv2 as _cv2
            except ImportError as exc:
                raise RuntimeError("Install the optional dependency 'opencv-python' to show the live window") from exc
            cv2 = _cv2

        try:
            while max_frames is None or processed_frames < max_frames:
                result = self.process_once()
                processed_frames += 1

                if cv2 is None:
                    continue

                cv2.imshow(window_name, result.rendered_frame[:, :, ::-1])
                key = cv2.waitKey(1) & 0xFF
                if key in {27, ord("q")}:
                    break
        finally:
            if cv2 is not None:
                cv2.destroyAllWindows()

        return processed_frames

    def close(self) -> None:
        self._capture.close()
