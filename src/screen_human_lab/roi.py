from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RoiRect:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def compute_center_square_roi(monitor: Mapping[str, int], requested_size: int) -> RoiRect:
    monitor_left = int(monitor.get("left", 0))
    monitor_top = int(monitor.get("top", 0))
    monitor_width = max(int(monitor.get("width", 0)), 0)
    monitor_height = max(int(monitor.get("height", 0)), 0)

    if requested_size < 1:
        raise ValueError("requested_size must be >= 1")
    if monitor_width < 1 or monitor_height < 1:
        raise ValueError("monitor must have positive width and height")

    effective_size = min(requested_size, monitor_width, monitor_height)
    left = monitor_left + (monitor_width - effective_size) // 2
    top = monitor_top + (monitor_height - effective_size) // 2
    return RoiRect(left=left, top=top, width=effective_size, height=effective_size)
