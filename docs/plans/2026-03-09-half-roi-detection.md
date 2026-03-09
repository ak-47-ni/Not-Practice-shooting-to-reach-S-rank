# Half ROI Detection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Shrink the real centered ROI detection area to `500x500` while restoring true-size detection boxes.

**Architecture:** Change the real ROI only at the preset/config boundary, remove the mistaken bbox-halving logic from the gated runtime, and keep overlay, `dx/dy`, and cursor-follow consuming the detector's true bbox inside the smaller ROI.

**Tech Stack:** Python 3.10+, `pytest`, YAML configs, existing capture/runtime/overlay stack

---

### Task 1: Restore true-size bbox behavior

**Files:**
- Modify: `src/screen_human_lab/pipeline/gated_runtime.py`
- Modify: `tests/test_gated_runtime.py`

**Step 1: Write the failing test**

```python
def test_runtime_selects_single_target_closest_to_roi_center() -> None:
    assert result.detections[0].bbox == original_bbox
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py -q`
Expected: FAIL because bbox shrinking is still active.

**Step 3: Write minimal implementation**

Remove the centered bbox-halving logic and keep the detector/tracker bbox unchanged through gated runtime output.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/pipeline/gated_runtime.py tests/test_gated_runtime.py
git commit -m "fix: restore true-size detection boxes"
```

### Task 2: Shrink real ROI presets to 500

**Files:**
- Modify: `configs/realtime_mps.yaml`
- Modify: `configs/realtime_mps_fast.yaml`
- Modify: `configs/realtime_mps_stable.yaml`
- Modify: `configs/realtime_cpu.yaml`
- Modify: `configs/realtime_cpu_fast.yaml`
- Modify: `configs/realtime_cpu_stable.yaml`
- Modify: `tests/test_cli_runtime.py`

**Step 1: Write the failing test**

```python
def test_default_configs_enable_overlay_roi_and_left_mouse_gate() -> None:
    assert "roi_size: 500" in mps_text
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_cli_runtime.py -q`
Expected: FAIL because the preset files still use `1000`.

**Step 3: Write minimal implementation**

Change the real runtime preset ROI size from `1000` to `500` for all interactive and CPU presets.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_cli_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add configs tests/test_cli_runtime.py
git commit -m "feat: shrink preset detection roi to 500"
```

### Task 3: Final regression verification

**Files:**
- Modify: `README.md`
- Test: `tests/test_overlay_control.py`
- Test: `tests/test_config.py`
- Test: `tests/test_gated_runtime.py`

**Step 1: Write the failing test**

```python
def test_runtime_uses_tracker_updates_while_locked() -> None:
    assert tracked_bbox == original_size_bbox
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py tests/test_cli_runtime.py -q`
Expected: FAIL until the old bbox shrink behavior is fully removed.

**Step 3: Write minimal implementation**

Finish the README wording so it describes smaller ROI rather than smaller detection boxes and verify config/cursor features still behave correctly.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md tests
git commit -m "test: verify half-roi detection workflow"
```
