from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import fmean


@dataclass(frozen=True)
class TimingSample:
    capture_ms: float
    inference_ms: float
    overlay_ms: float
    total_ms: float


class RollingMetrics:
    def __init__(self, window_size: int = 30) -> None:
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        self._samples: deque[TimingSample] = deque(maxlen=window_size)

    def add(self, sample: TimingSample) -> None:
        self._samples.append(sample)

    def summary(self) -> dict[str, float]:
        if not self._samples:
            return {
                "capture_ms": 0.0,
                "inference_ms": 0.0,
                "overlay_ms": 0.0,
                "total_ms": 0.0,
                "fps": 0.0,
            }

        capture_ms = fmean(sample.capture_ms for sample in self._samples)
        inference_ms = fmean(sample.inference_ms for sample in self._samples)
        overlay_ms = fmean(sample.overlay_ms for sample in self._samples)
        total_ms = fmean(sample.total_ms for sample in self._samples)
        fps = 0.0 if total_ms <= 0 else 1000.0 / total_ms

        return {
            "capture_ms": capture_ms,
            "inference_ms": inference_ms,
            "overlay_ms": overlay_ms,
            "total_ms": total_ms,
            "fps": fps,
        }
