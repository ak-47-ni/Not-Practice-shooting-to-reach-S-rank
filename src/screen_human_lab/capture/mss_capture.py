from __future__ import annotations

import numpy as np

from screen_human_lab.config import CaptureConfig
from screen_human_lab.roi import RoiRect, compute_center_square_roi


class MSSCapture:
    def __init__(self, config: CaptureConfig) -> None:
        try:
            from mss import mss
        except ImportError as exc:
            raise RuntimeError("Install the optional dependency 'mss' for screen capture support") from exc

        self._config = config
        self._session = mss()
        self._monitor_rect = self._resolve_monitor_rect()
        self._roi_rect = compute_center_square_roi(
            {"left": self._monitor_rect.left, "top": self._monitor_rect.top, "width": self._monitor_rect.width, "height": self._monitor_rect.height},
            self._config.roi_size,
        )

    @property
    def monitor_rect(self) -> RoiRect:
        if not hasattr(self, "_monitor_rect"):
            self._monitor_rect = self._resolve_monitor_rect()
        return self._monitor_rect

    @property
    def roi_rect(self) -> RoiRect:
        if not hasattr(self, "_roi_rect"):
            rect = self.monitor_rect
            self._roi_rect = compute_center_square_roi(
                {"left": rect.left, "top": rect.top, "width": rect.width, "height": rect.height},
                self._config.roi_size,
            )
        return self._roi_rect

    def _resolve_monitor_rect(self) -> RoiRect:
        monitors = list(getattr(self._session, "monitors", []))
        requested_monitor = self._config.monitor

        if len(monitors) <= requested_monitor:
            actual_monitors = max(len(monitors) - 1, 0)
            raise RuntimeError(
                "No usable monitor is available for capture. "
                f"Requested monitor index {requested_monitor}, but mss reported {actual_monitors} actual monitor(s). "
                "Check screen recording permission and whether this process can see an active desktop session."
            )

        monitor = monitors[requested_monitor]
        if int(monitor.get("width", 0)) <= 0 or int(monitor.get("height", 0)) <= 0:
            raise RuntimeError(
                "No usable monitor is available for capture. "
                f"Monitor index {requested_monitor} has size {monitor.get('width', 0)}x{monitor.get('height', 0)}. "
                "Check screen recording permission and whether this process can see an active desktop session."
            )

        return RoiRect(
            left=int(monitor.get("left", 0)),
            top=int(monitor.get("top", 0)),
            width=int(monitor.get("width", 0)),
            height=int(monitor.get("height", 0)),
        )

    def grab(self) -> np.ndarray:
        rect = self.roi_rect
        monitor = {"left": rect.left, "top": rect.top, "width": rect.width, "height": rect.height}
        frame = np.array(self._session.grab(monitor), dtype=np.uint8)[:, :, :3]
        return frame[:, :, ::-1].copy()

    def globalize_bbox(self, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = bbox
        rect = self.roi_rect
        return (rect.left + x1, rect.top + y1, rect.left + x2, rect.top + y2)

    def close(self) -> None:
        close = getattr(self._session, "close", None)
        if callable(close):
            close()
