from __future__ import annotations

import json
from collections.abc import Iterator

import numpy as np

from screen_human_lab.pipeline.recording import RoiRecordingSession, SamplingAction
from screen_human_lab.roi import RoiRect


class _FakeCapture:
    roi_rect = RoiRect(left=10, top=20, width=4, height=3)

    def __init__(self) -> None:
        self.frames_grabbed = 0
        self.closed = False

    def grab(self) -> np.ndarray:
        self.frames_grabbed += 1
        return np.full((3, 4, 3), self.frames_grabbed, dtype=np.uint8)

    def close(self) -> None:
        self.closed = True


def test_roi_recording_session_writes_images_and_manifest(tmp_path) -> None:
    capture = _FakeCapture()
    session = RoiRecordingSession(
        capture=capture,
        output_dir=tmp_path,
        config_name="configs/realtime_win_cuda.yaml",
        interval_frames=2,
        filename_prefix="roi",
    )

    saved = session.run(max_frames=5)

    assert saved == 3
    images = sorted((tmp_path / "images").glob("*.png"))
    assert [image.name for image in images] == [
        "roi_000001.png",
        "roi_000003.png",
        "roi_000005.png",
    ]

    records = [
        json.loads(line)
        for line in (tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [record["frame_index"] for record in records] == [1, 3, 5]
    assert records[0]["roi_rect"] == {"left": 10, "top": 20, "width": 4, "height": 3}
    assert records[0]["config_name"] == "configs/realtime_win_cuda.yaml"
    assert records[0]["label_state"] == "unlabeled"
    assert records[0]["image_path"] == "images/roi_000001.png"
    assert capture.closed is True


def test_roi_recording_session_rejects_invalid_interval(tmp_path) -> None:
    try:
        RoiRecordingSession(capture=_FakeCapture(), output_dir=tmp_path, interval_frames=0)
    except ValueError as exc:
        assert "interval_frames" in str(exc)
    else:
        raise AssertionError("expected invalid interval to fail")


def test_manual_roi_recording_saves_only_requested_samples(tmp_path) -> None:
    capture = _FakeCapture()
    actions: Iterator[SamplingAction] = iter(
        [
            SamplingAction.SKIP,
            SamplingAction.POSITIVE,
            SamplingAction.NEGATIVE,
            SamplingAction.HARD,
            SamplingAction.QUIT,
        ]
    )
    session = RoiRecordingSession(
        capture=capture,
        output_dir=tmp_path,
        config_name="configs/realtime_win_cuda.yaml",
        action_provider=lambda _frame_index: next(actions),
    )

    saved = session.run_manual()

    assert saved == 3
    assert capture.frames_grabbed == 5
    images = sorted((tmp_path / "images").glob("*.png"))
    assert [image.name for image in images] == [
        "hard_000004.png",
        "negative_000003.png",
        "positive_000002.png",
    ]

    records = [
        json.loads(line)
        for line in (tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [record["label_state"] for record in records] == ["positive", "negative", "hard"]
    assert [record["frame_index"] for record in records] == [2, 3, 4]


def test_sampling_action_from_key_maps_supported_keys() -> None:
    assert SamplingAction.from_key("p") is SamplingAction.POSITIVE
    assert SamplingAction.from_key("N") is SamplingAction.NEGATIVE
    assert SamplingAction.from_key("h") is SamplingAction.HARD
    assert SamplingAction.from_key("q") is SamplingAction.QUIT
    assert SamplingAction.from_key("\x1b") is SamplingAction.QUIT
    assert SamplingAction.from_key("x") is SamplingAction.SKIP
