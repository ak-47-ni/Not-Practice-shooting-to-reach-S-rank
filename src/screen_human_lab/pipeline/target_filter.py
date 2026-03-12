from __future__ import annotations


class TargetStateFilter:
    def __init__(self, *, smoothing_factor: float = 0.35) -> None:
        self._smoothing_factor = smoothing_factor
        self._state: tuple[float, float, float, float] | None = None

    def reset(self) -> None:
        self._state = None

    def update(self, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        if self._state is None or self._smoothing_factor <= 0.0:
            self._state = tuple(float(value) for value in bbox)
            return bbox

        alpha = self._smoothing_factor
        updated = tuple((1.0 - alpha) * previous + (alpha * float(current)) for previous, current in zip(self._state, bbox, strict=False))
        self._state = updated
        return tuple(int(round(value)) for value in updated)
