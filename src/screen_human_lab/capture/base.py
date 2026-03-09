from __future__ import annotations

from typing import Protocol

import numpy as np

from screen_human_lab.roi import RoiRect


class FrameCapture(Protocol):
    roi_rect: RoiRect

    def grab(self) -> np.ndarray:
        ...

    def globalize_bbox(self, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        ...

    def close(self) -> None:
        ...
