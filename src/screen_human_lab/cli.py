from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, MutableMapping
from pathlib import Path

from screen_human_lab.capture.imagegrab_capture import ImageGrabCapture
from screen_human_lab.capture.mss_capture import MSSCapture
from screen_human_lab.config import CaptureConfig, TrackingConfig, load_config
from screen_human_lab.inference.factory import build_backend
from screen_human_lab.pipeline.runtime import RuntimeSession, StablePreviewSession
from screen_human_lab.tracking.template_match import TemplateMatchTracker


Execvpe = Callable[[str, list[str], dict[str, str]], None]
TrackerFactory = Callable[[], TemplateMatchTracker]



def build_capture(config: CaptureConfig):
    if config.provider == "mss":
        return MSSCapture(config)
    if config.provider == "imagegrab":
        return ImageGrabCapture(config)
    raise ValueError(f"Unsupported capture provider: {config.provider}")



def build_tracker_factory(config: TrackingConfig) -> TrackerFactory:
    def _factory() -> TemplateMatchTracker:
        return TemplateMatchTracker(
            match_threshold=config.match_threshold,
            search_padding=config.search_padding,
            max_search_padding=config.max_search_padding,
            prediction_gain=config.prediction_gain,
        )

    return _factory



def should_use_macos_overlay(*, headless: bool, overlay_mode: str, platform: str | None = None) -> bool:
    resolved_platform = sys.platform if platform is None else platform
    return (not headless) and resolved_platform == "darwin" and overlay_mode == "overlay"


def should_use_windows_overlay(*, headless: bool, overlay_mode: str, platform: str | None = None) -> bool:
    resolved_platform = sys.platform if platform is None else platform
    return (not headless) and resolved_platform == "win32" and overlay_mode == "overlay"



def maybe_reexec_for_mps_fallback(
    *,
    preferred_backend: str,
    argv: list[str],
    env: MutableMapping[str, str] | None = None,
    execvpe: Execvpe = os.execvpe,
    executable: str | None = None,
    platform: str | None = None,
) -> bool:
    resolved_platform = sys.platform if platform is None else platform
    runtime_env = os.environ if env is None else env
    if resolved_platform != "darwin":
        return False
    if preferred_backend not in {"auto", "mps"}:
        return False
    if runtime_env.get("PYTORCH_ENABLE_MPS_FALLBACK"):
        return False

    runtime_env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    target_executable = sys.executable if executable is None else executable
    execvpe(target_executable, [target_executable, "-m", "screen_human_lab.cli", *argv], dict(runtime_env))
    return True



def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Controlled-lab screen capture and detection research tool")
    parser.add_argument("--config", type=Path, required=True, help="Path to YAML config file")
    parser.add_argument("--max-frames", type=int, default=None, help="Stop after N frames")
    parser.add_argument("--headless", action="store_true", help="Disable the interactive overlay and preview window")
    return parser



def _run_headless_preview(
    *,
    capture,
    backend,
    tracker_factory,
    stability_config,
    enable_overlay: bool,
    max_frames: int | None,
    window_name: str,
    headless: bool,
) -> int:
    if stability_config.enabled:
        session = StablePreviewSession(
            capture=capture,
            backend=backend,
            tracker_factory=tracker_factory,
            stability_config=stability_config,
            enable_overlay=enable_overlay,
        )
    else:
        session = RuntimeSession(
            capture=capture,
            backend=backend,
            enable_overlay=enable_overlay,
        )
    try:
        processed = session.run(
            max_frames=max_frames,
            show_window=not headless,
            window_name=window_name,
        )
    finally:
        session.close()
    return processed



def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    cli_args = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(cli_args)

    config = load_config(args.config)
    maybe_reexec_for_mps_fallback(preferred_backend=config.inference.backend, argv=cli_args)

    capture = build_capture(config.capture)
    backend = build_backend(config.inference)
    tracker_factory = build_tracker_factory(config.tracking)

    if should_use_windows_overlay(headless=args.headless, overlay_mode=config.overlay.mode):
        from screen_human_lab.overlay.windows_overlay import run_overlay_session

        try:
            return run_overlay_session(
                capture=capture,
                backend=backend,
                target_fps=config.capture.target_fps,
                infer_only_while_right_mouse_down=config.overlay.infer_only_while_right_mouse_down,
                cursor_follow_speed=config.overlay.cursor_follow_speed,
                cursor_follow_min_distance=config.overlay.cursor_follow_min_distance,
                tracker_factory=tracker_factory,
                stability_config=config.stability,
            )
        finally:
            capture.close()

    if should_use_macos_overlay(headless=args.headless, overlay_mode=config.overlay.mode):
        from screen_human_lab.overlay.appkit_overlay import run_overlay_session

        try:
            return run_overlay_session(
                capture=capture,
                backend=backend,
                target_fps=config.capture.target_fps,
                infer_only_while_right_mouse_down=config.overlay.infer_only_while_right_mouse_down,
                cursor_follow_speed=config.overlay.cursor_follow_speed,
                cursor_follow_min_distance=config.overlay.cursor_follow_min_distance,
                tracker_factory=tracker_factory,
                stability_config=config.stability,
            )
        finally:
            capture.close()

    processed = _run_headless_preview(
        capture=capture,
        backend=backend,
        tracker_factory=tracker_factory,
        stability_config=config.stability,
        enable_overlay=config.overlay.enabled,
        max_frames=args.max_frames,
        window_name=config.window_name,
        headless=args.headless,
    )
    print(f"Processed {processed} frame(s) with backend={backend.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
