from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


ADAPTIVE_PADDING_VELOCITY_SCALE = 2.0


@dataclass(frozen=True)
class TrackingResult:
    success: bool
    bbox: tuple[int, int, int, int] | None
    score: float


class TemplateMatchTracker:
    def __init__(
        self,
        *,
        match_threshold: float = 0.45,
        search_padding: int = 24,
        max_search_padding: int | None = None,
        prediction_gain: float = 0.0,
    ) -> None:
        self._match_threshold = match_threshold
        self._search_padding = search_padding
        self._max_search_padding = search_padding if max_search_padding is None else max(max_search_padding, search_padding)
        self._prediction_gain = prediction_gain
        self._bbox: tuple[int, int, int, int] | None = None
        self._template_gray: np.ndarray | None = None
        self._velocity_x = 0.0
        self._velocity_y = 0.0

    def initialize(self, frame: np.ndarray, bbox: tuple[int, int, int, int]) -> None:
        gray = _to_gray(frame)
        clipped_bbox = _clip_bbox(bbox, frame.shape[1], frame.shape[0])
        x1, y1, x2, y2 = clipped_bbox
        if x2 - x1 < 2 or y2 - y1 < 2:
            raise ValueError("tracker bbox must have width and height >= 2")

        self._bbox = clipped_bbox
        self._template_gray = gray[y1:y2, x1:x2].copy()
        self._velocity_x = 0.0
        self._velocity_y = 0.0

    def update(self, frame: np.ndarray) -> TrackingResult:
        if self._bbox is None or self._template_gray is None:
            return TrackingResult(success=False, bbox=None, score=0.0)

        gray = _to_gray(frame)
        predicted_bbox = _shift_bbox(
            self._bbox,
            delta_x=self._velocity_x * self._prediction_gain,
            delta_y=self._velocity_y * self._prediction_gain,
        )
        x1, y1, x2, y2 = predicted_bbox
        template_height, template_width = self._template_gray.shape
        padding = _compute_adaptive_padding(
            base_padding=self._search_padding,
            max_padding=self._max_search_padding,
            velocity_x=self._velocity_x,
            velocity_y=self._velocity_y,
        )
        pad_x = max(padding, template_width // 2)
        pad_y = max(padding, template_height // 2)

        search_left = max(0, x1 - pad_x)
        search_top = max(0, y1 - pad_y)
        search_right = min(gray.shape[1], x2 + pad_x)
        search_bottom = min(gray.shape[0], y2 + pad_y)
        search_region = gray[search_top:search_bottom, search_left:search_right]

        if search_region.shape[0] < template_height or search_region.shape[1] < template_width:
            return TrackingResult(success=False, bbox=None, score=0.0)

        result = cv2.matchTemplate(search_region, self._template_gray, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if np.isnan(max_val) or max_val < self._match_threshold:
            return TrackingResult(success=False, bbox=None, score=float(max_val) if not np.isnan(max_val) else 0.0)

        new_x1 = search_left + int(max_loc[0])
        new_y1 = search_top + int(max_loc[1])
        new_bbox = _clip_bbox((new_x1, new_y1, new_x1 + template_width, new_y1 + template_height), frame.shape[1], frame.shape[0])
        previous_center_x, previous_center_y = _bbox_center(self._bbox)
        new_center_x, new_center_y = _bbox_center(new_bbox)
        self._velocity_x = new_center_x - previous_center_x
        self._velocity_y = new_center_y - previous_center_y
        self._bbox = new_bbox
        return TrackingResult(success=True, bbox=self._bbox, score=float(max_val))

    def clear(self) -> None:
        self._bbox = None
        self._template_gray = None
        self._velocity_x = 0.0
        self._velocity_y = 0.0



def _to_gray(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)



def _clip_bbox(bbox: tuple[int, int, int, int], frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    clipped_x1 = min(max(int(x1), 0), frame_width - 1)
    clipped_y1 = min(max(int(y1), 0), frame_height - 1)
    clipped_x2 = min(max(int(x2), clipped_x1 + 1), frame_width)
    clipped_y2 = min(max(int(y2), clipped_y1 + 1), frame_height)
    return (clipped_x1, clipped_y1, clipped_x2, clipped_y2)



def _bbox_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)



def _shift_bbox(bbox: tuple[int, int, int, int], *, delta_x: float, delta_y: float) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    shift_x = int(round(delta_x))
    shift_y = int(round(delta_y))
    return (x1 + shift_x, y1 + shift_y, x2 + shift_x, y2 + shift_y)



def _compute_adaptive_padding(*, base_padding: int, max_padding: int, velocity_x: float, velocity_y: float) -> int:
    speed = max(abs(velocity_x), abs(velocity_y))
    expanded_padding = base_padding + int(round(speed * ADAPTIVE_PADDING_VELOCITY_SCALE))
    return min(max_padding, max(base_padding, expanded_padding))
