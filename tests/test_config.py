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
    assert select_runtime_backend("auto", mps_available=True) == "mps"


def test_select_runtime_backend_falls_back_to_cpu_when_mps_unavailable() -> None:
    assert select_runtime_backend("auto", mps_available=False) == "cpu"


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
