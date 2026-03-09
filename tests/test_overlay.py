import numpy as np

from screen_human_lab.inference.base import Detection
from screen_human_lab.pipeline.overlay import render_overlay


def test_overlay_preserves_frame_shape() -> None:
    frame = np.zeros((24, 24, 3), dtype=np.uint8)

    rendered = render_overlay(
        frame,
        [Detection(label="person", confidence=0.9, bbox=(2, 2, 10, 10))],
        {"fps": 60.0, "capture_ms": 1.0, "inference_ms": 4.0, "overlay_ms": 1.0, "total_ms": 8.0},
        backend_name="onnx-cpu",
        frame_index=1,
    )

    assert rendered.shape == frame.shape


def test_overlay_draws_box_pixels() -> None:
    frame = np.zeros((24, 24, 3), dtype=np.uint8)

    rendered = render_overlay(
        frame,
        [Detection(label="person", confidence=0.9, bbox=(2, 2, 10, 10))],
        {"fps": 60.0, "capture_ms": 1.0, "inference_ms": 4.0, "overlay_ms": 1.0, "total_ms": 8.0},
        backend_name="onnx-cpu",
        frame_index=1,
    )

    assert rendered[2, 2].any()
