from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_metadata_files_exist() -> None:
    assert (ROOT / "README.md").exists()
    assert (ROOT / "pyproject.toml").exists()
    assert (ROOT / ".gitignore").exists()


def test_runtime_config_files_exist() -> None:
    assert (ROOT / "configs" / "realtime_mps.yaml").exists()
    assert (ROOT / "configs" / "realtime_cpu.yaml").exists()
    assert (ROOT / "configs" / "realtime_win_cuda.yaml").exists()
    assert (ROOT / "configs" / "realtime_win_cpu.yaml").exists()


def test_readme_mentions_taichi_py_conda_environment() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Taichi_py" in readme_text


def test_readme_mentions_windows_preview_workflow() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Windows" in readme_text
    assert "realtime_win_cuda.yaml" in readme_text
    assert "preview" in readme_text


def test_pyproject_supports_taichi_py_python_version() -> None:
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'requires-python = ">=3.10,<3.14"' in pyproject_text


def test_pyproject_pins_numpy_below_2_for_torch_compatibility() -> None:
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"numpy>=1.26,<2"' in pyproject_text


def test_pyproject_pins_opencv_below_4_12_for_numpy_1_compatibility() -> None:
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"opencv-python>=4.10.0,<4.12"' in pyproject_text


def test_pyproject_declares_pyobjc_cocoa_for_overlay() -> None:
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "\"pyobjc-framework-Cocoa>=10.3\"" in pyproject_text


def test_pyproject_declares_cuda_optional_dependencies() -> None:
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "cuda = [" in pyproject_text
    assert '"torch>=2.5.0"' in pyproject_text
    assert '"ultralytics>=8.3.0"' in pyproject_text


def test_test_plan_mentions_right_mouse_gated_detection() -> None:
    test_plan_text = (ROOT / "docs" / "testing" / "test-plan.md").read_text(encoding="utf-8")

    assert "right mouse" in test_plan_text


def test_readme_mentions_l_hotkey_toggle() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "press `L`" in readme_text


def test_test_plan_mentions_l_hotkey_toggle() -> None:
    test_plan_text = (ROOT / "docs" / "testing" / "test-plan.md").read_text(encoding="utf-8")

    assert "press `L`" in test_plan_text


def test_readme_mentions_single_target_lock_and_5_frame_recovery() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "single target" in readme_text
    assert "5 lost frames" in readme_text


def test_test_plan_mentions_single_target_lock_and_5_frame_recovery() -> None:
    test_plan_text = (ROOT / "docs" / "testing" / "test-plan.md").read_text(encoding="utf-8")

    assert "single target" in test_plan_text
    assert "5 lost frames" in test_plan_text



def test_tracking_preset_files_exist() -> None:
    assert (ROOT / "configs" / "realtime_mps_stable.yaml").exists()
    assert (ROOT / "configs" / "realtime_mps_fast.yaml").exists()
    assert (ROOT / "configs" / "realtime_cpu_stable.yaml").exists()
    assert (ROOT / "configs" / "realtime_cpu_fast.yaml").exists()


def test_windows_cuda_config_uses_preview_mode() -> None:
    config_text = (ROOT / "configs" / "realtime_win_cuda.yaml").read_text(encoding="utf-8")

    assert "backend: auto" in config_text
    assert "mode: preview" in config_text
    assert "stability:" in config_text


def test_tracking_preset_files_define_tracking_keys() -> None:
    stable_text = (ROOT / "configs" / "realtime_mps_stable.yaml").read_text(encoding="utf-8")
    fast_text = (ROOT / "configs" / "realtime_cpu_fast.yaml").read_text(encoding="utf-8")

    assert "tracking:" in stable_text
    assert "match_threshold:" in stable_text
    assert "search_padding:" in stable_text
    assert "max_search_padding:" in stable_text
    assert "prediction_gain:" in stable_text
    assert "tracking:" in fast_text
    assert "match_threshold:" in fast_text
    assert "search_padding:" in fast_text
    assert "max_search_padding:" in fast_text
    assert "prediction_gain:" in fast_text


def test_readme_mentions_stable_and_fast_tracking_presets() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "stable" in readme_text
    assert "fast" in readme_text
    assert "match_threshold" in readme_text
    assert "adaptive" in readme_text
    assert "prediction_gain" in readme_text


def test_test_plan_mentions_tracking_presets() -> None:
    test_plan_text = (ROOT / "docs" / "testing" / "test-plan.md").read_text(encoding="utf-8")

    assert "tracking" in test_plan_text
    assert "stable" in test_plan_text
    assert "fast" in test_plan_text
    assert "adaptive" in test_plan_text



def test_readme_mentions_dx_dy_overlay() -> None:
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "dx=" in readme_text
    assert "dy=" in readme_text


def test_test_plan_mentions_dx_dy_overlay() -> None:
    test_plan_text = (ROOT / "docs" / "testing" / "test-plan.md").read_text(encoding="utf-8")

    assert "dx/dy" in test_plan_text


def test_windows_overlay_config_exists() -> None:
    assert (ROOT / "configs" / "realtime_win_overlay_cuda.yaml").exists()


def test_windows_overlay_config_uses_overlay_mode() -> None:
    config_text = (ROOT / "configs" / "realtime_win_overlay_cuda.yaml").read_text(encoding="utf-8")

    assert "mode: overlay" in config_text
    assert "infer_only_while_right_mouse_down: true" in config_text
