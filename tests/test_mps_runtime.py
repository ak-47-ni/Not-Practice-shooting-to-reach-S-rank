import os

from screen_human_lab.inference.torch_mps import configure_mps_runtime_env


def test_configure_mps_runtime_env_enables_cpu_fallback_by_default() -> None:
    env = {}

    configure_mps_runtime_env(env)

    assert env["PYTORCH_ENABLE_MPS_FALLBACK"] == "1"


def test_configure_mps_runtime_env_preserves_existing_setting() -> None:
    env = {"PYTORCH_ENABLE_MPS_FALLBACK": "0"}

    configure_mps_runtime_env(env)

    assert env["PYTORCH_ENABLE_MPS_FALLBACK"] == "0"
