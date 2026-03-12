from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Sequence

from screen_human_lab.inference.base import Detection


@dataclass(frozen=True)
class ScoringWeights:
    confidence_weight: float = 0.8
    iou_weight: float = 1.6
    distance_weight: float = 0.9
    size_weight: float = 0.2



def select_best_detection(
    detections: Sequence[Detection],
    *,
    frame_shape: tuple[int, ...],
    predicted_bbox: tuple[int, int, int, int] | None = None,
    weights: ScoringWeights | None = None,
) -> Detection | None:
    if not detections:
        return None

    resolved_weights = weights or ScoringWeights()
    scored = [
        (
            _score_detection(
                detection,
                frame_shape=frame_shape,
                predicted_bbox=predicted_bbox,
                weights=resolved_weights,
            ),
            detection,
        )
        for detection in detections
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]



def _score_detection(
    detection: Detection,
    *,
    frame_shape: tuple[int, ...],
    predicted_bbox: tuple[int, int, int, int] | None,
    weights: ScoringWeights,
) -> float:
    confidence_score = detection.confidence * weights.confidence_weight
    if predicted_bbox is None:
        reference_center = (frame_shape[1] / 2.0, frame_shape[0] / 2.0)
        iou_score = 0.0
        size_score = 0.0
    else:
        reference_center = _bbox_center(predicted_bbox)
        iou_score = _bbox_iou(detection.bbox, predicted_bbox) * weights.iou_weight
        size_score = _size_similarity(detection.bbox, predicted_bbox) * weights.size_weight

    distance = hypot(_bbox_center(detection.bbox)[0] - reference_center[0], _bbox_center(detection.bbox)[1] - reference_center[1])
    max_distance = max(float(frame_shape[0]), float(frame_shape[1]), 1.0)
    distance_score = max(0.0, 1.0 - (distance / max_distance)) * weights.distance_weight
    return confidence_score + iou_score + size_score + distance_score



def _bbox_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)



def _bbox_iou(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> float:
    first_x1, first_y1, first_x2, first_y2 = first
    second_x1, second_y1, second_x2, second_y2 = second
    inter_x1 = max(first_x1, second_x1)
    inter_y1 = max(first_y1, second_y1)
    inter_x2 = min(first_x2, second_x2)
    inter_y2 = min(first_y2, second_y2)
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    intersection = float((inter_x2 - inter_x1) * (inter_y2 - inter_y1))
    first_area = float((first_x2 - first_x1) * (first_y2 - first_y1))
    second_area = float((second_x2 - second_x1) * (second_y2 - second_y1))
    union = first_area + second_area - intersection
    return 0.0 if union <= 0.0 else intersection / union



def _size_similarity(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> float:
    first_area = max(float((first[2] - first[0]) * (first[3] - first[1])), 1.0)
    second_area = max(float((second[2] - second[0]) * (second[3] - second[1])), 1.0)
    ratio = min(first_area, second_area) / max(first_area, second_area)
    return max(0.0, min(1.0, ratio))
