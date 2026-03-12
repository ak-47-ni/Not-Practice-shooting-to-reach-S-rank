from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MotionEstimate:
    delta_x: float = 0.0
    delta_y: float = 0.0
    confidence: float = 0.0

    @property
    def magnitude(self) -> float:
        return float(np.hypot(self.delta_x, self.delta_y))


class GlobalMotionEstimator:
    def __init__(self, *, max_magnitude: float | None = 128.0) -> None:
        self._max_magnitude = max_magnitude

    def estimate(self, previous_frame: np.ndarray | None, current_frame: np.ndarray) -> MotionEstimate:
        if previous_frame is None or previous_frame.shape != current_frame.shape:
            return MotionEstimate()

        previous_gray = _to_gray(previous_frame)
        current_gray = _to_gray(current_frame)
        if previous_gray.size == 0 or current_gray.size == 0:
            return MotionEstimate()

        delta_x, delta_y, confidence = _phase_correlation(previous_gray, current_gray)
        if self._max_magnitude is not None:
            magnitude = float(np.hypot(delta_x, delta_y))
            if magnitude > self._max_magnitude:
                return MotionEstimate(confidence=0.0)
        return MotionEstimate(delta_x=delta_x, delta_y=delta_y, confidence=confidence)



def _to_gray(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame.astype(np.float32)
    red = frame[..., 0].astype(np.float32)
    green = frame[..., 1].astype(np.float32)
    blue = frame[..., 2].astype(np.float32)
    return (0.299 * red) + (0.587 * green) + (0.114 * blue)



def _phase_correlation(previous_gray: np.ndarray, current_gray: np.ndarray) -> tuple[float, float, float]:
    previous_fft = np.fft.fft2(previous_gray)
    current_fft = np.fft.fft2(current_gray)
    cross_power = previous_fft * np.conjugate(current_fft)
    magnitude = np.abs(cross_power)
    cross_power /= np.where(magnitude == 0.0, 1.0, magnitude)
    correlation = np.fft.ifft2(cross_power)
    correlation_abs = np.abs(correlation)
    peak_index = np.unravel_index(np.argmax(correlation_abs), correlation_abs.shape)
    peak_value = float(correlation_abs[peak_index])

    height, width = previous_gray.shape
    peak_y = float(peak_index[0])
    peak_x = float(peak_index[1])
    if peak_y > height / 2.0:
        peak_y -= float(height)
    if peak_x > width / 2.0:
        peak_x -= float(width)

    confidence = 0.0 if correlation_abs.sum() == 0.0 else peak_value / float(correlation_abs.sum())
    return (-peak_x, -peak_y, confidence)
