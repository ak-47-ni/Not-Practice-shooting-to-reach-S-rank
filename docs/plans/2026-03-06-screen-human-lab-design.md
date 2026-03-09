# Screen Human Lab Design

**Date:** 2026-03-06

**Goal:** Build a Python research framework for real-time screen capture and human detection in controlled lab settings, without any input injection or automation.

## Scope

- Real-time screen capture on macOS.
- Zero-training prototype using pre-trained detectors.
- Dual inference routes:
  - Apple GPU route via `MPS`.
  - CPU fallback route via `ONNX Runtime`.
- On-screen overlay and performance metrics.
- Explicitly excludes mouse movement, input control, memory inspection, and game automation.

## Architecture

The project uses a modular streaming pipeline:

1. `Capture` acquires frames from the desktop.
2. `Preprocess` normalizes frames to the detector input size.
3. `Inference Backend` runs a pre-trained person detector.
4. `Overlay` renders detections, labels, and runtime metrics.
5. `Runtime` coordinates frame processing and benchmark logging.

The same pipeline is shared across two backends so results are comparable under the same capture and visualization logic.

## Backend Strategy

### Primary backend: Apple GPU / MPS

- Intended for this machine (`Apple M2`, `Metal Supported`).
- Loads a local PyTorch-compatible detector on `mps`.
- Best for low-latency interactive research.

### Fallback backend: ONNX CPU

- Runs on machines without a usable accelerator.
- Loads a local ONNX model through `onnxruntime`.
- Provides a stable baseline for reproducible benchmarking.

## Project Layout

- `configs/`: runtime presets for `mps` and `cpu`
- `src/screen_human_lab/capture/`: frame acquisition abstractions
- `src/screen_human_lab/inference/`: backend interface and implementations
- `src/screen_human_lab/pipeline/`: preprocessing, metrics, overlay, runtime loop
- `tests/`: unit tests for config, backend selection, metrics, and runtime orchestration
- `artifacts/`: optional runtime outputs and benchmark logs

## Runtime Flow

1. Load YAML config.
2. Build capture source.
3. Build inference backend.
4. Pull a frame.
5. Run detection.
6. Draw overlay.
7. Record timing metrics.
8. Repeat until exit.

## Safety Boundaries

- Only screen capture and visualization are in scope.
- No system input APIs are invoked.
- No game process memory, hooks, or injection points are used.
- The framework is suitable for offline research, benchmarks, and controlled lab validation.

## Validation Plan

- Unit tests cover config loading, backend selection, metrics smoothing, and loop orchestration.
- Optional dependencies are imported lazily so tests can run without installing heavy ML packages.
- Runtime smoke tests are documented in the README for when the user installs dependencies locally.

## Environment Notes

- The system default `Python 3.14` remains too new for parts of the ML stack.
- The project is aligned to the local `Taichi_py` conda environment, currently `Python 3.10.15`, for practical setup.
