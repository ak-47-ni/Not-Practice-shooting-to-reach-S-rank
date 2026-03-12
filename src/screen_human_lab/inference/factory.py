from __future__ import annotations

from collections.abc import Callable, Mapping

from screen_human_lab.config import InferenceConfig, is_cuda_available, is_mps_available, select_runtime_backend
from screen_human_lab.inference.base import InferenceBackend


BackendBuilder = Callable[[InferenceConfig], InferenceBackend]


def _default_backend_builders() -> dict[str, BackendBuilder]:
    from screen_human_lab.inference.onnx_cpu import OnnxCpuBackend
    from screen_human_lab.inference.torch_cuda import TorchCudaBackend
    from screen_human_lab.inference.torch_mps import TorchMpsBackend

    return {
        "cuda": TorchCudaBackend,
        "mps": TorchMpsBackend,
        "cpu": OnnxCpuBackend,
    }



def build_backend(
    config: InferenceConfig,
    *,
    cuda_available: bool | None = None,
    mps_available: bool | None = None,
    backend_builders: Mapping[str, BackendBuilder] | None = None,
) -> InferenceBackend:
    selected_backend = select_runtime_backend(
        config.backend,
        cuda_available=is_cuda_available() if cuda_available is None else cuda_available,
        mps_available=is_mps_available() if mps_available is None else mps_available,
    )
    builders = dict(backend_builders) if backend_builders is not None else _default_backend_builders()

    if selected_backend not in builders:
        raise ValueError(f"No backend builder registered for '{selected_backend}'")

    builder = builders[selected_backend]
    try:
        return builder(config)
    except ImportError as exc:
        raise RuntimeError(
            f"Install the optional dependency for the '{selected_backend}' backend before running it: {exc}"
        ) from exc
