from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from screen_human_lab.inference.base import Detection

try:
    import cv2
except ImportError:
    cv2 = None



def render_overlay(
    frame: np.ndarray,
    detections: Sequence[Detection],
    metrics: Mapping[str, float],
    *,
    backend_name: str,
    frame_index: int,
    debug_lines: Sequence[str] | None = None,
) -> np.ndarray:
    canvas = frame.copy()

    for detection in detections:
        _draw_box(canvas, detection.bbox)

    _draw_header(
        canvas,
        backend_name=backend_name,
        fps=metrics.get("fps", 0.0),
        frame_index=frame_index,
        debug_lines=debug_lines or (),
    )
    return canvas



def _draw_box(frame: np.ndarray, bbox: tuple[int, int, int, int], color: tuple[int, int, int] = (0, 255, 0)) -> None:
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, width - 1))
    x2 = max(0, min(x2, width - 1))
    y1 = max(0, min(y1, height - 1))
    y2 = max(0, min(y2, height - 1))

    if x2 <= x1 or y2 <= y1:
        return

    frame[y1 : min(y1 + 2, height), x1 : x2 + 1] = color
    frame[max(y2 - 1, 0) : y2 + 1, x1 : x2 + 1] = color
    frame[y1 : y2 + 1, x1 : min(x1 + 2, width)] = color
    frame[y1 : y2 + 1, max(x2 - 1, 0) : x2 + 1] = color



def _draw_header(
    frame: np.ndarray,
    *,
    backend_name: str,
    fps: float,
    frame_index: int,
    debug_lines: Sequence[str],
) -> None:
    line_count = 1 + len(debug_lines)
    banner_height = min(18 * line_count, frame.shape[0])
    frame[0:banner_height, 0 : min(frame.shape[1], 240)] = (20, 20, 20)

    if cv2 is None:
        return

    lines = [f"#{frame_index} {backend_name} {fps:.1f} fps", *debug_lines]
    for index, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (4, 13 + (index * 16)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
