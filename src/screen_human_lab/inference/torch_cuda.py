from __future__ import annotations

import numpy as np

from screen_human_lab.config import InferenceConfig
from screen_human_lab.inference.base import Detection


class TorchCudaBackend:
    name = "torch-cuda"
    device = "cuda"

    def __init__(self, config: InferenceConfig) -> None:
        if not config.model_path:
            raise ValueError("model_path is required for the CUDA backend")

        try:
            import torch
            from ultralytics import YOLO
        except ImportError as exc:
            raise ImportError("Missing dependencies for the CUDA backend") from exc

        if not torch.cuda.is_available():
            raise RuntimeError("PyTorch CUDA is not available on this machine")

        self._model = YOLO(config.model_path)
        self._confidence_threshold = config.confidence_threshold
        self._input_size = config.input_size

    def predict(self, frame: np.ndarray) -> list[Detection]:
        results = self._model.predict(
            source=frame,
            verbose=False,
            device=self.device,
            conf=self._confidence_threshold,
            imgsz=self._input_size,
            classes=[0],
        )
        return _parse_ultralytics_results(results)



def _parse_ultralytics_results(results) -> list[Detection]:
    detections: list[Detection] = []
    if not results:
        return detections

    boxes = getattr(results[0], "boxes", None)
    if boxes is None:
        return detections

    xyxy = boxes.xyxy.int().cpu().tolist()
    confidences = boxes.conf.cpu().tolist()
    for bbox, confidence in zip(xyxy, confidences, strict=False):
        x1, y1, x2, y2 = bbox
        detections.append(
            Detection(label="person", confidence=float(confidence), bbox=(int(x1), int(y1), int(x2), int(y2)))
        )
    return detections
