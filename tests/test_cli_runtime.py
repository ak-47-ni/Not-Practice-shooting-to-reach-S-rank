from pathlib import Path

from screen_human_lab.config import TrackingConfig
from screen_human_lab.cli import build_tracker_factory, maybe_reexec_for_mps_fallback, should_use_macos_overlay


ROOT = Path(__file__).resolve().parents[1]


def test_maybe_reexec_for_mps_fallback_reexecs_for_auto_backend() -> None:
    calls: list[tuple[str, list[str], dict[str, str]]] = []

    def fake_exec(executable: str, args: list[str], env: dict[str, str]) -> None:
        calls.append((executable, args, env))
        raise SystemExit(0)

    try:
        maybe_reexec_for_mps_fallback(
            preferred_backend="auto",
            argv=["--config", "configs/realtime_mps.yaml"],
            env={},
            execvpe=fake_exec,
            executable="python-test",
        )
    except SystemExit:
        pass

    assert len(calls) == 1
    assert calls[0][0] == "python-test"
    assert calls[0][1] == ["python-test", "-m", "screen_human_lab.cli", "--config", "configs/realtime_mps.yaml"]
    assert calls[0][2]["PYTORCH_ENABLE_MPS_FALLBACK"] == "1"


def test_maybe_reexec_for_mps_fallback_skips_when_env_already_set() -> None:
    called = False

    def fake_exec(executable: str, args: list[str], env: dict[str, str]) -> None:
        nonlocal called
        called = True

    result = maybe_reexec_for_mps_fallback(
        preferred_backend="mps",
        argv=["--config", "configs/realtime_mps.yaml"],
        env={"PYTORCH_ENABLE_MPS_FALLBACK": "1"},
        execvpe=fake_exec,
        executable="python-test",
    )

    assert result is False
    assert called is False


def test_maybe_reexec_for_mps_fallback_skips_for_cpu_backend() -> None:
    called = False

    def fake_exec(executable: str, args: list[str], env: dict[str, str]) -> None:
        nonlocal called
        called = True

    result = maybe_reexec_for_mps_fallback(
        preferred_backend="cpu",
        argv=["--config", "configs/realtime_cpu.yaml"],
        env={},
        execvpe=fake_exec,
        executable="python-test",
    )

    assert result is False
    assert called is False


def test_should_use_macos_overlay_respects_headless_and_mode() -> None:
    assert should_use_macos_overlay(headless=False, overlay_mode="overlay") is True
    assert should_use_macos_overlay(headless=True, overlay_mode="overlay") is False
    assert should_use_macos_overlay(headless=False, overlay_mode="preview") is False


def test_default_configs_enable_overlay_roi_and_right_mouse_gate() -> None:
    mps_text = (ROOT / "configs" / "realtime_mps.yaml").read_text(encoding="utf-8")
    cpu_text = (ROOT / "configs" / "realtime_cpu.yaml").read_text(encoding="utf-8")

    assert "roi_size: 500" in mps_text
    assert "mode: overlay" in mps_text
    assert "infer_only_while_right_mouse_down: true" in mps_text
    assert "cursor_follow_speed:" in mps_text
    assert "cursor_follow_min_distance:" in mps_text
    assert "roi_size: 500" in cpu_text
    assert "mode: overlay" in cpu_text
    assert "infer_only_while_right_mouse_down: true" in cpu_text
    assert "cursor_follow_speed:" in cpu_text
    assert "cursor_follow_min_distance:" in cpu_text



def test_build_tracker_factory_uses_tracking_config_values() -> None:
    factory = build_tracker_factory(TrackingConfig(match_threshold=0.55, search_padding=36, max_search_padding=96, prediction_gain=1.4))

    tracker = factory()

    assert tracker._match_threshold == 0.55
    assert tracker._search_padding == 36
    assert tracker._max_search_padding == 96
    assert tracker._prediction_gain == 1.4
