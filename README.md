# Screen Human Lab

`Screen Human Lab` is a Python research framework for controlled-lab experiments involving centered ROI screen capture and person detection.

## Research Scope

- Real-time centered ROI screen capture
- Zero-training experiments with pre-trained detectors
- Dual backend support:
  - Apple GPU via `MPS`
  - CPU fallback via `ONNX Runtime`
- Transparent overlay rendering on macOS
- Right mouse gated inference to reduce idle resource usage
- Configurable straight-line cursor follow toward the locked target center while the left mouse button is held

## Out of Scope

- Memory inspection
- Game hooks or automation

## Recommended Environment

Use the local conda environment at `python` for this project. It currently provides `Python 3.10.15`, which is compatible with the lightweight project skeleton and the planned runtime stack. For the current `torch` wheel set in this environment, keep `numpy` below `2.0` to avoid the NumPy ABI mismatch warning at import time.

Activate it by path because `conda run -n Taichi_py` does not currently resolve on this machine:

```bash
conda activate python
python -m pip install --upgrade pip
python -m pip install -e ".[runtime,mps,dev]"
# if pip resolves OpenCV too new, keep it below 4.12 to stay compatible with numpy<2
```

For CPU-only validation in the same environment:

```bash
python -m pip install -e ".[runtime,cpu,dev]"
```

## Model Files

Place local detector weights under `models/`.

- `models/yolo11n.pt` for the `MPS` route
- `models/yolo11n.onnx` for the `CPU` route

The project intentionally does not download model weights automatically.

## Run

Headless single-frame smoke test:

```bash
python -m screen_human_lab.cli --config configs/realtime_mps.yaml --max-frames 1 --headless
```

Interactive overlay mode:

```bash
python -m screen_human_lab.cli --config configs/realtime_mps.yaml
```

CPU route:

```bash
python -m screen_human_lab.cli --config configs/realtime_cpu.yaml --headless --max-frames 10
```

Tracking presets:

```bash
python -m screen_human_lab.cli --config configs/realtime_mps_stable.yaml
python -m screen_human_lab.cli --config configs/realtime_mps_fast.yaml
python -m screen_human_lab.cli --config configs/realtime_cpu_stable.yaml --headless --max-frames 10
python -m screen_human_lab.cli --config configs/realtime_cpu_fast.yaml --headless --max-frames 10
```

- `stable`: adaptive lock preset with `match_threshold=0.55`, `search_padding=36`, `max_search_padding=96`, `prediction_gain=1.4`, tuned to stay steadier while still following fast motion
- `fast`: adaptive lock preset with `match_threshold=0.45`, `search_padding=24`, `max_search_padding=56`, `prediction_gain=0.9`, tuned to be lighter and faster

Interactive mode captures only the centered square ROI, draws a thin ROI outline plus detection boxes in a transparent overlay, and only performs inference while the right mouse button is pressed. The current realtime presets use a `500x500` centered ROI. Each right-mouse hold locks at most one single target, keeps tracking only that target, and only falls back to re-detection after more than 5 lost frames. Detection boxes are rendered at their true tracked size inside that smaller ROI. While a target is locked and the left mouse button is held, the system cursor follows the locked target center along a straight-line path based on the current cursor-to-target vector. If the current cursor position cannot be read, the runtime falls back to the ROI center as the reference point. Tune `overlay.cursor_follow_speed` in the YAML config to adjust how quickly the cursor closes the remaining distance, and `overlay.cursor_follow_min_distance` to control how close the cursor must get before it stops moving. The overlay also shows `dx=...  dy=...` in the top-right corner while a target is locked, using screen-style signs where `+dx` is right and `+dy` is down. press `L` to toggle the detection service on or off; the ROI border stays visible and changes color to show the current state.

On the current `Taichi_py` environment, the CLI will automatically relaunch itself with `PYTORCH_ENABLE_MPS_FALLBACK=1` when you use the `auto` or `mps` backend, because `torchvision::nms` falls back to CPU on this machine.

## Project Layout

- `configs/`: runtime presets
- `src/screen_human_lab/capture/`: screen capture adapters
- `src/screen_human_lab/inference/`: inference abstractions and backends
- `src/screen_human_lab/pipeline/`: metrics, overlay, runtime loop
- `tests/`: unit tests for the skeleton
- `docs/plans/`: design and implementation planning docs

## Verification

Unit tests can run directly in `Taichi_py`:

```bash
conda run -p python -m pytest -q
```
