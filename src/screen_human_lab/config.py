from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_BACKENDS = {"auto", "mps", "cpu"}
SUPPORTED_CAPTURE_PROVIDERS = {"mss", "imagegrab"}
SUPPORTED_OVERLAY_MODES = {"preview", "overlay"}


DEFAULT_TRACKING_MATCH_THRESHOLD = 0.45
DEFAULT_TRACKING_SEARCH_PADDING = 24
DEFAULT_TRACKING_PREDICTION_GAIN = 0.0
DEFAULT_CURSOR_FOLLOW_SPEED = 4000.0
DEFAULT_CURSOR_FOLLOW_MIN_DISTANCE = 1.0


def is_mps_available() -> bool:
    try:
        import torch
    except ImportError:
        return False

    mps_backend = getattr(getattr(torch, "backends", object()), "mps", None)
    return bool(mps_backend and mps_backend.is_available())



def select_runtime_backend(preferred: str, mps_available: bool | None = None) -> str:
    if preferred not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend '{preferred}'. Expected one of {sorted(SUPPORTED_BACKENDS)}")

    if preferred != "auto":
        return preferred

    available = is_mps_available() if mps_available is None else mps_available
    return "mps" if available else "cpu"


@dataclass(frozen=True)
class CaptureConfig:
    provider: str = "mss"
    monitor: int = 1
    target_fps: int = 30
    roi_size: int = 1000

    def __post_init__(self) -> None:
        if self.provider not in SUPPORTED_CAPTURE_PROVIDERS:
            raise ValueError(
                f"Unsupported capture provider '{self.provider}'. Expected one of {sorted(SUPPORTED_CAPTURE_PROVIDERS)}"
            )
        if self.monitor < 1:
            raise ValueError("monitor must be >= 1")
        if self.target_fps < 1:
            raise ValueError("target_fps must be >= 1")
        if self.roi_size < 32:
            raise ValueError("roi_size must be >= 32")


@dataclass(frozen=True)
class InferenceConfig:
    backend: str = "auto"
    model_path: str | None = None
    confidence_threshold: float = 0.25
    input_size: int = 640

    def __post_init__(self) -> None:
        select_runtime_backend(self.backend, mps_available=False)
        if self.model_path is not None and not self.model_path.strip():
            raise ValueError("model_path cannot be empty")
        if not 0.0 < self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be within (0.0, 1.0]")
        if self.input_size < 64:
            raise ValueError("input_size must be >= 64")


@dataclass(frozen=True)
class OverlayConfig:
    enabled: bool = True
    show_fps: bool = True
    show_backend: bool = True
    mode: str = "overlay"
    infer_only_while_right_mouse_down: bool = True
    cursor_follow_speed: float = DEFAULT_CURSOR_FOLLOW_SPEED
    cursor_follow_min_distance: float = DEFAULT_CURSOR_FOLLOW_MIN_DISTANCE

    def __post_init__(self) -> None:
        if self.mode not in SUPPORTED_OVERLAY_MODES:
            raise ValueError(f"Unsupported overlay mode '{self.mode}'. Expected one of {sorted(SUPPORTED_OVERLAY_MODES)}")
        if self.cursor_follow_speed <= 0.0:
            raise ValueError("cursor_follow_speed must be > 0.0")
        if self.cursor_follow_min_distance < 0.0:
            raise ValueError("cursor_follow_min_distance must be >= 0.0")


@dataclass(frozen=True)
class TrackingConfig:
    match_threshold: float = DEFAULT_TRACKING_MATCH_THRESHOLD
    search_padding: int = DEFAULT_TRACKING_SEARCH_PADDING
    max_search_padding: int | None = None
    prediction_gain: float = DEFAULT_TRACKING_PREDICTION_GAIN

    def __post_init__(self) -> None:
        if not 0.0 < self.match_threshold <= 1.0:
            raise ValueError("match_threshold must be within (0.0, 1.0]")
        if self.search_padding < 0:
            raise ValueError("search_padding must be >= 0")
        resolved_max_search_padding = self.search_padding if self.max_search_padding is None else self.max_search_padding
        if resolved_max_search_padding < self.search_padding:
            raise ValueError("max_search_padding must be >= search_padding")
        if self.prediction_gain < 0.0:
            raise ValueError("prediction_gain must be >= 0.0")
        object.__setattr__(self, "max_search_padding", resolved_max_search_padding)


@dataclass(frozen=True)
class AppConfig:
    window_name: str = "Screen Human Lab"
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)



def _ensure_mapping(value: Any, section_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section '{section_name}' must be a mapping")
    return value



def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("Top-level config must be a mapping")

    capture_payload = _ensure_mapping(payload.get("capture"), "capture")
    inference_payload = _ensure_mapping(payload.get("inference"), "inference")
    overlay_payload = _ensure_mapping(payload.get("overlay"), "overlay")
    if (
        "infer_only_while_left_mouse_down" in overlay_payload
        and "infer_only_while_right_mouse_down" not in overlay_payload
    ):
        overlay_payload = dict(overlay_payload)
        overlay_payload["infer_only_while_right_mouse_down"] = overlay_payload.pop("infer_only_while_left_mouse_down")
    tracking_payload = _ensure_mapping(payload.get("tracking"), "tracking")

    return AppConfig(
        window_name=str(payload.get("window_name", "Screen Human Lab")),
        capture=CaptureConfig(**capture_payload),
        inference=InferenceConfig(**inference_payload),
        overlay=OverlayConfig(**overlay_payload),
        tracking=TrackingConfig(**tracking_payload),
    )
