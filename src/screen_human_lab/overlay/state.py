from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from threading import Lock

from screen_human_lab.inference.base import Detection
from screen_human_lab.roi import RoiRect


@dataclass(frozen=True)
class OverlaySnapshot:
    roi_rect: RoiRect
    detections: list[Detection]
    active: bool
    service_enabled: bool


@dataclass(frozen=True)
class DetectionOffset:
    dx: int
    dy: int


DEFAULT_CURSOR_MIN_DISTANCE = 1.0


class OverlayState:
    def __init__(self, *, roi_rect: RoiRect) -> None:
        self._lock = Lock()
        self._roi_rect = roi_rect
        self._detections: list[Detection] = []
        self._active = False
        self._service_enabled = True

    def set_roi_rect(self, roi_rect: RoiRect) -> None:
        with self._lock:
            self._roi_rect = roi_rect

    def set_active(self, active: bool) -> None:
        with self._lock:
            self._active = active

    def set_service_enabled(self, service_enabled: bool) -> None:
        with self._lock:
            self._service_enabled = service_enabled

    def set_detections(self, detections: list[Detection]) -> None:
        with self._lock:
            self._detections = list(detections)

    def clear_detections(self) -> None:
        with self._lock:
            self._detections = []

    def snapshot(self) -> OverlaySnapshot:
        with self._lock:
            return OverlaySnapshot(
                roi_rect=self._roi_rect,
                detections=list(self._detections),
                active=self._active,
                service_enabled=self._service_enabled,
            )



def compute_detection_offset(*, roi_rect: RoiRect, detection: Detection) -> DetectionOffset:
    roi_center_x = roi_rect.left + (roi_rect.width / 2.0)
    roi_center_y = roi_rect.top + (roi_rect.height / 2.0)
    x1, y1, x2, y2 = detection.bbox
    target_center_x = (x1 + x2) / 2.0
    target_center_y = (y1 + y2) / 2.0
    return DetectionOffset(
        dx=int(round(target_center_x - roi_center_x)),
        dy=int(round(target_center_y - roi_center_y)),
    )



def format_detection_offset(offset: DetectionOffset) -> str:
    return f"dx={offset.dx:+d}  dy={offset.dy:+d}"



def build_detection_offset_label(*, roi_rect: RoiRect, detections: list[Detection]) -> str | None:
    if not detections:
        return None
    return format_detection_offset(compute_detection_offset(roi_rect=roi_rect, detection=detections[0]))


def compute_cursor_step(
    *,
    delta_x: float,
    delta_y: float,
    speed_pixels_per_second: float,
    delta_time: float,
    min_distance: float = DEFAULT_CURSOR_MIN_DISTANCE,
) -> tuple[float, float]:
    if speed_pixels_per_second <= 0.0:
        raise ValueError("speed_pixels_per_second must be > 0.0")
    if delta_time < 0.0:
        raise ValueError("delta_time must be >= 0.0")
    if min_distance < 0.0:
        raise ValueError("min_distance must be >= 0.0")

    distance = hypot(delta_x, delta_y)
    if distance <= min_distance or delta_time == 0.0:
        return (0.0, 0.0)

    travel_distance = speed_pixels_per_second * delta_time
    if travel_distance >= distance:
        return (delta_x, delta_y)

    scale = travel_distance / distance
    return (delta_x * scale, delta_y * scale)
