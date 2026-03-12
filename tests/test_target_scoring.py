from screen_human_lab.inference.base import Detection
from screen_human_lab.pipeline.target_scoring import select_best_detection


def test_select_best_detection_prefers_overlap_with_predicted_bbox() -> None:
    detections = [
        Detection(label="person", confidence=0.6, bbox=(22, 22, 62, 62)),
        Detection(label="person", confidence=0.95, bbox=(90, 90, 130, 130)),
    ]

    best = select_best_detection(
        detections,
        frame_shape=(160, 160, 3),
        predicted_bbox=(20, 20, 60, 60),
    )

    assert best == detections[0]


def test_select_best_detection_uses_roi_center_without_prediction() -> None:
    detections = [
        Detection(label="person", confidence=0.9, bbox=(0, 0, 20, 20)),
        Detection(label="person", confidence=0.7, bbox=(70, 70, 110, 110)),
    ]

    best = select_best_detection(detections, frame_shape=(180, 180, 3))

    assert best == detections[1]
