from pathlib import Path

import pytest

from screen_human_lab.config import load_config, select_runtime_backend


def test_load_config_parses_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
window_name: Demo
capture:
  provider: mss
  monitor: 2
  target_fps: 20
  roi_size: 900
inference:
  backend: auto
  model_path: models/demo.pt
  confidence_threshold: 0.4
  input_size: 512
overlay:
  enabled: true
  show_fps: true
  show_backend: false
  mode: overlay
  infer_only_while_right_mouse_down: true
  cursor_follow_speed: 5000.0
  cursor_follow_min_distance: 0.5
tracking:
  match_threshold: 0.55
  search_padding: 36
  max_search_padding: 96
  prediction_gain: 1.4
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.window_name == "Demo"
    assert config.capture.monitor == 2
    assert config.capture.target_fps == 20
    assert config.capture.roi_size == 900
    assert config.inference.model_path == "models/demo.pt"
    assert config.inference.input_size == 512
    assert config.overlay.show_backend is False
    assert config.overlay.mode == "overlay"
    assert config.overlay.infer_only_while_right_mouse_down is True
    assert config.overlay.cursor_follow_speed == 5000.0
    assert config.overlay.cursor_follow_min_distance == 0.5
    assert config.tracking.match_threshold == 0.55
    assert config.tracking.search_padding == 36
    assert config.tracking.max_search_padding == 96
    assert config.tracking.prediction_gain == 1.4


def test_select_runtime_backend_prefers_mps_when_available() -> None:
    assert select_runtime_backend("auto", cuda_available=False, mps_available=True, platform="darwin") == "mps"


def test_select_runtime_backend_prefers_cuda_when_available() -> None:
    assert select_runtime_backend("auto", cuda_available=True, mps_available=False, platform="win32") == "cuda"


def test_select_runtime_backend_falls_back_to_cpu_when_mps_unavailable() -> None:
    assert select_runtime_backend("auto", cuda_available=False, mps_available=False, platform="win32") == "cpu"


def test_select_runtime_backend_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unsupported backend"):
        select_runtime_backend("mps-or-cpu")



def test_load_config_defaults_tracking_when_section_is_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("window_name: Demo\n", encoding="utf-8")

    config = load_config(config_path)

    assert config.tracking.match_threshold == 0.45
    assert config.tracking.search_padding == 24
    assert config.tracking.max_search_padding == 24
    assert config.tracking.prediction_gain == 0.0
    assert config.overlay.cursor_follow_speed == 4000.0
    assert config.overlay.cursor_follow_min_distance == 1.0
    assert config.stability.enabled is True
    assert config.stability.enable_global_motion is True
    assert config.stability.max_lost_frames == 5
    assert config.stability.smoothing_factor == 0.35


def test_load_config_parses_stability_section(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
window_name: Demo
stability:
  enabled: true
  enable_global_motion: false
  max_lost_frames: 7
  confidence_weight: 0.8
  iou_weight: 1.6
  distance_weight: 0.9
  size_weight: 0.2
  smoothing_factor: 0.25
  switch_margin: 0.18
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.stability.enabled is True
    assert config.stability.enable_global_motion is False
    assert config.stability.max_lost_frames == 7
    assert config.stability.confidence_weight == 0.8
    assert config.stability.iou_weight == 1.6
    assert config.stability.distance_weight == 0.9
    assert config.stability.size_weight == 0.2
    assert config.stability.smoothing_factor == 0.25
    assert config.stability.switch_margin == 0.18
