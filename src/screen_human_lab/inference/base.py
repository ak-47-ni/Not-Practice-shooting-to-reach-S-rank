from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]


class InferenceBackend(Protocol):
    name: str
    device: str

    def predict(self, frame: np.ndarray) -> list[Detection]:
        ...
