import pytest

from screen_human_lab.pipeline.metrics import RollingMetrics, TimingSample


def test_rolling_metrics_computes_average_summary() -> None:
    metrics = RollingMetrics(window_size=2)
    metrics.add(TimingSample(capture_ms=2.0, inference_ms=5.0, overlay_ms=1.0, total_ms=10.0))
    metrics.add(TimingSample(capture_ms=4.0, inference_ms=7.0, overlay_ms=1.0, total_ms=20.0))

    summary = metrics.summary()

    assert summary["capture_ms"] == pytest.approx(3.0)
    assert summary["inference_ms"] == pytest.approx(6.0)
    assert summary["overlay_ms"] == pytest.approx(1.0)
    assert summary["total_ms"] == pytest.approx(15.0)
    assert summary["fps"] == pytest.approx(1000.0 / 15.0)


def test_rolling_metrics_returns_zeroes_when_empty() -> None:
    summary = RollingMetrics(window_size=3).summary()

    assert summary == {
        "capture_ms": 0.0,
        "inference_ms": 0.0,
        "overlay_ms": 0.0,
        "total_ms": 0.0,
        "fps": 0.0,
    }
