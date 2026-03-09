from __future__ import annotations

from collections.abc import Callable, Sequence
from threading import Lock
from typing import Protocol

from screen_human_lab.inference.base import Detection
from screen_human_lab.overlay.state import DEFAULT_CURSOR_MIN_DISTANCE, compute_cursor_step
from screen_human_lab.roi import RoiRect


DEFAULT_TOGGLE_KEY = "l"
DEFAULT_CURSOR_FOLLOW_SPEED = 4000.0


class CursorMover(Protocol):
    def move_to(self, target_x: float, target_y: float) -> None:
        ...


CursorPositionProvider = Callable[[], tuple[float, float]]
FallbackPositionProvider = Callable[[RoiRect], tuple[float, float]]
TargetPositionProvider = Callable[[Detection, RoiRect], tuple[float, float]]


class OverlayControl:
    def __init__(self, *, service_enabled: bool = True) -> None:
        self._lock = Lock()
        self._service_enabled = service_enabled

    @property
    def service_enabled(self) -> bool:
        with self._lock:
            return self._service_enabled

    def toggle_service(self) -> bool:
        with self._lock:
            self._service_enabled = not self._service_enabled
            return self._service_enabled

    def compute_active(self, *, right_mouse_down: bool, infer_only_while_right_mouse_down: bool) -> bool:
        with self._lock:
            service_enabled = self._service_enabled

        if not service_enabled:
            return False
        if not infer_only_while_right_mouse_down:
            return True
        return right_mouse_down


class CursorFollowController:
    def __init__(
        self,
        *,
        mover: CursorMover,
        cursor_position_provider: CursorPositionProvider,
        fallback_position_provider: FallbackPositionProvider,
        target_position_provider: TargetPositionProvider,
        speed_pixels_per_second: float = DEFAULT_CURSOR_FOLLOW_SPEED,
        min_distance: float = DEFAULT_CURSOR_MIN_DISTANCE,
    ) -> None:
        self._mover = mover
        self._cursor_position_provider = cursor_position_provider
        self._fallback_position_provider = fallback_position_provider
        self._target_position_provider = target_position_provider
        self._speed_pixels_per_second = speed_pixels_per_second
        self._min_distance = min_distance
        self._last_known_position: tuple[float, float] | None = None

    def update(self, *, active: bool, roi_rect: RoiRect, detections: Sequence[Detection], delta_time: float) -> bool:
        if not active or not detections:
            return False

        current_x, current_y = self._resolve_current_position(roi_rect)
        target_x, target_y = self._target_position_provider(detections[0], roi_rect)
        step_x, step_y = compute_cursor_step(
            delta_x=target_x - current_x,
            delta_y=target_y - current_y,
            speed_pixels_per_second=self._speed_pixels_per_second,
            delta_time=delta_time,
            min_distance=self._min_distance,
        )
        if step_x == 0.0 and step_y == 0.0:
            return False

        next_position = (current_x + step_x, current_y + step_y)
        self._mover.move_to(*next_position)
        self._last_known_position = next_position
        return True

    def _resolve_current_position(self, roi_rect: RoiRect) -> tuple[float, float]:
        try:
            current_x, current_y = self._cursor_position_provider()
        except Exception:
            return self._resolve_fallback_position(roi_rect)

        if current_x is None or current_y is None:
            return self._resolve_fallback_position(roi_rect)
        resolved_position = (float(current_x), float(current_y))
        self._last_known_position = resolved_position
        return resolved_position

    def _resolve_fallback_position(self, roi_rect: RoiRect) -> tuple[float, float]:
        if self._last_known_position is not None:
            return self._last_known_position
        fallback_position = self._fallback_position_provider(roi_rect)
        resolved_position = (float(fallback_position[0]), float(fallback_position[1]))
        self._last_known_position = resolved_position
        return resolved_position


def should_toggle_for_characters(characters: str | None, toggle_key: str = DEFAULT_TOGGLE_KEY) -> bool:
    if not characters:
        return False
    return characters.casefold() == toggle_key.casefold()
