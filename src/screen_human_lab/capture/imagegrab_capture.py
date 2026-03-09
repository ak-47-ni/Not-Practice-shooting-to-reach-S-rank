from __future__ import annotations

import numpy as np

from screen_human_lab.config import CaptureConfig


class ImageGrabCapture:
    def __init__(self, config: CaptureConfig) -> None:
        try:
            from PIL import ImageGrab
        except ImportError as exc:
            raise RuntimeError("Install the optional dependency 'Pillow' for ImageGrab support") from exc

        self._image_grab = ImageGrab
        self._config = config

    def grab(self) -> np.ndarray:
        image = self._image_grab.grab()
        return np.array(image, dtype=np.uint8)

    def close(self) -> None:
        return None
