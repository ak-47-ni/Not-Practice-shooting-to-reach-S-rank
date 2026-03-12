import numpy as np
import pytest

from screen_human_lab.config import InferenceConfig
from screen_human_lab.inference.base import Detection
from screen_human_lab.inference.factory import build_backend


class _FakeBackend:
    def __init__(self, name: str, device: str) -> None:
        self.name = name
        self.device = device

    def predict(self, frame: np.ndarray) -> list[Detection]:
        return []


def test_build_backend_uses_explicit_backend_builder() -> None:
    config = InferenceConfig(backend="mps", model_path="models/demo.pt")

    backend = build_backend(
        config,
        mps_available=False,
        backend_builders={
            "mps": lambda _: _FakeBackend("torch-mps", "mps"),
            "cpu": lambda _: _FakeBackend("onnx-cpu", "cpu"),
        },
    )

    assert backend.name == "torch-mps"
    assert backend.device == "mps"


def test_build_backend_uses_explicit_cuda_builder() -> None:
    config = InferenceConfig(backend="cuda", model_path="models/demo.pt")

    backend = build_backend(
        config,
        cuda_available=True,
        mps_available=False,
        backend_builders={
            "cuda": lambda _: _FakeBackend("torch-cuda", "cuda"),
            "mps": lambda _: _FakeBackend("torch-mps", "mps"),
            "cpu": lambda _: _FakeBackend("onnx-cpu", "cpu"),
        },
    )

    assert backend.name == "torch-cuda"
    assert backend.device == "cuda"


def test_build_backend_uses_auto_selected_cuda_builder() -> None:
    config = InferenceConfig(backend="auto", model_path="models/demo.pt")

    backend = build_backend(
        config,
        cuda_available=True,
        mps_available=False,
        backend_builders={
            "cuda": lambda _: _FakeBackend("torch-cuda", "cuda"),
            "mps": lambda _: _FakeBackend("torch-mps", "mps"),
            "cpu": lambda _: _FakeBackend("onnx-cpu", "cpu"),
        },
    )

    assert backend.name == "torch-cuda"
    assert backend.device == "cuda"


def test_build_backend_uses_auto_selected_cpu_builder() -> None:
    config = InferenceConfig(backend="auto", model_path="models/demo.onnx")

    backend = build_backend(
        config,
        cuda_available=False,
        mps_available=False,
        backend_builders={
            "cuda": lambda _: _FakeBackend("torch-cuda", "cuda"),
            "mps": lambda _: _FakeBackend("torch-mps", "mps"),
            "cpu": lambda _: _FakeBackend("onnx-cpu", "cpu"),
        },
    )

    assert backend.name == "onnx-cpu"
    assert backend.device == "cpu"


def test_build_backend_raises_actionable_error_for_missing_optional_dependency() -> None:
    config = InferenceConfig(backend="mps", model_path="models/demo.pt")

    def _broken_builder(_: InferenceConfig) -> _FakeBackend:
        raise ImportError("No module named 'ultralytics'")

    with pytest.raises(RuntimeError, match="Install the optional dependency"):
        build_backend(
            config,
            cuda_available=False,
            mps_available=True,
            backend_builders={
                "cuda": lambda _: _FakeBackend("torch-cuda", "cuda"),
                "mps": _broken_builder,
                "cpu": lambda _: _FakeBackend("onnx-cpu", "cpu"),
            },
        )
