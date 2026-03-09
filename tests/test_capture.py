from types import SimpleNamespace

import pytest

from screen_human_lab.capture.mss_capture import MSSCapture
from screen_human_lab.config import CaptureConfig
from screen_human_lab.roi import RoiRect


def test_mss_capture_globalizes_detection_bbox_from_roi() -> None:
    capture = object.__new__(MSSCapture)
    capture._config = CaptureConfig(provider="mss", monitor=1, target_fps=5, roi_size=1000)
    capture._roi_rect = RoiRect(left=200, top=300, width=956, height=956)

    assert capture.globalize_bbox((10, 20, 30, 40)) == (210, 320, 230, 340)


def test_mss_capture_raises_actionable_error_when_monitor_is_missing() -> None:
    capture = object.__new__(MSSCapture)
    capture._config = CaptureConfig(provider="mss", monitor=1, target_fps=5, roi_size=1000)
    capture._session = SimpleNamespace(monitors=[{"left": 0, "top": 0, "width": 0, "height": 0}])

    with pytest.raises(RuntimeError, match="No usable monitor"):
        capture.grab()


def test_mss_capture_exposes_monitor_rect_metadata() -> None:
    capture = object.__new__(MSSCapture)
    capture._monitor_rect = RoiRect(left=0, top=0, width=1470, height=956)

    assert capture.monitor_rect == RoiRect(left=0, top=0, width=1470, height=956)
