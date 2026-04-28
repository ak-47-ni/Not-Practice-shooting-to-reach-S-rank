from __future__ import annotations

import json
import sys
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from screen_human_lab.capture.base import FrameCapture


class SamplingAction(str, Enum):
    SKIP = "skip"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    HARD = "hard"
    QUIT = "quit"

    @classmethod
    def from_key(cls, key: str | None) -> "SamplingAction":
        if key is None:
            return cls.SKIP
        normalized = key.casefold()
        if normalized == "p":
            return cls.POSITIVE
        if normalized == "n":
            return cls.NEGATIVE
        if normalized == "h":
            return cls.HARD
        if normalized == "q" or key == "\x1b":
            return cls.QUIT
        return cls.SKIP


ActionProvider = Callable[[int], SamplingAction]


class RoiRecordingSession:
    def __init__(
        self,
        *,
        capture: FrameCapture,
        output_dir: str | Path,
        config_name: str | None = None,
        interval_frames: int = 1,
        filename_prefix: str = "roi",
        label_state: str = "unlabeled",
        action_provider: ActionProvider | None = None,
    ) -> None:
        if interval_frames < 1:
            raise ValueError("interval_frames must be >= 1")
        if not filename_prefix.strip():
            raise ValueError("filename_prefix cannot be empty")

        self._capture = capture
        self._output_dir = Path(output_dir)
        self._image_dir = self._output_dir / "images"
        self._manifest_path = self._output_dir / "manifest.jsonl"
        self._config_name = config_name
        self._interval_frames = interval_frames
        self._filename_prefix = filename_prefix
        self._label_state = label_state
        self._action_provider = action_provider or _read_sampling_action

    def run(self, *, max_frames: int | None = None) -> int:
        saved_count = 0
        frame_index = 0
        self._image_dir.mkdir(parents=True, exist_ok=True)
        try:
            while max_frames is None or frame_index < max_frames:
                frame_index += 1
                frame = self._capture.grab()
                if (frame_index - 1) % self._interval_frames != 0:
                    continue

                self._save_frame(frame, frame_index=frame_index, label_state=self._label_state, filename_prefix=self._filename_prefix)
                saved_count += 1
        finally:
            self._capture.close()
        return saved_count

    def run_manual(self, *, max_frames: int | None = None) -> int:
        saved_count = 0
        frame_index = 0
        self._image_dir.mkdir(parents=True, exist_ok=True)
        try:
            while max_frames is None or frame_index < max_frames:
                frame_index += 1
                frame = self._capture.grab()
                action = self._action_provider(frame_index)
                if action is SamplingAction.QUIT:
                    break
                if action is SamplingAction.SKIP:
                    continue

                self._save_frame(frame, frame_index=frame_index, label_state=action.value, filename_prefix=action.value)
                saved_count += 1
        finally:
            self._capture.close()
        return saved_count

    def _append_manifest(self, record: dict[str, Any]) -> None:
        with self._manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def _save_frame(
        self,
        frame: np.ndarray,
        *,
        frame_index: int,
        label_state: str,
        filename_prefix: str,
    ) -> None:
        image_name = f"{filename_prefix}_{frame_index:06d}.png"
        image_path = self._image_dir / image_name
        _write_png(image_path, frame)
        self._append_manifest(
            {
                "frame_index": frame_index,
                "image_path": f"images/{image_name}",
                "roi_rect": _serialize_roi_rect(self._capture.roi_rect),
                "config_name": self._config_name,
                "label_state": label_state,
            }
        )


def _write_png(path: Path, frame: np.ndarray) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Install the optional dependency 'Pillow' to record ROI images") from exc

    Image.fromarray(frame).save(path)


def _serialize_roi_rect(roi_rect) -> dict[str, int]:
    return {
        "left": int(roi_rect.left),
        "top": int(roi_rect.top),
        "width": int(roi_rect.width),
        "height": int(roi_rect.height),
    }


def _read_sampling_action(_frame_index: int) -> SamplingAction:
    print("[p] positive  [n] negative  [h] hard  [Enter] skip  [q/Esc] quit: ", end="", flush=True)
    key = _read_single_key()
    print()
    return SamplingAction.from_key(key)


def _read_single_key() -> str:
    if sys.platform == "win32":
        import msvcrt

        return msvcrt.getwch()

    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
