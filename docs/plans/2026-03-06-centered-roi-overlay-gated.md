# Centered ROI Overlay Gated Detection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a center-ROI, transparent-overlay workflow that only performs detection while the left mouse button is pressed.

**Architecture:** Add a reusable ROI geometry layer, convert capture to ROI-only mode, introduce a gated detection service, and replace the OpenCV preview window with a macOS overlay window that draws only ROI and detection boxes. Keep the existing inference backends, but move the interactive path onto overlay-driven rendering and input gating.

**Tech Stack:** Python 3.10+, `mss`, `numpy`, `PyYAML`, optional `torch`, optional `ultralytics`, optional `pyobjc-framework-Cocoa`, `pytest`

---

### Task 1: Add ROI configuration and geometry helpers

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/config.py`
- Create: `screen-human-lab/src/screen_human_lab/roi.py`
- Test: `screen-human-lab/tests/test_roi.py`
- Test: `screen-human-lab/tests/test_config.py`

**Step 1: Write the failing test**

```python
def test_compute_center_square_roi_falls_back_to_monitor_height():
    roi = compute_center_square_roi({"left": 0, "top": 0, "width": 1470, "height": 956}, 1000)
    assert roi.width == 956
```

**Step 2: Run test to verify it fails**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_roi.py tests/test_config.py -q`
Expected: FAIL because ROI helpers and config fields do not exist yet.

**Step 3: Write minimal implementation**

Add `roi_size`, overlay mode settings, and a small ROI dataclass plus centered square calculation helper.

**Step 4: Run test to verify it passes**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_roi.py tests/test_config.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/config.py src/screen_human_lab/roi.py tests/test_roi.py tests/test_config.py
 git commit -m "feat: add centered roi configuration"
```

### Task 2: Convert MSS capture to ROI-only mode

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/capture/mss_capture.py`
- Modify: `screen-human-lab/src/screen_human_lab/capture/base.py`
- Test: `screen-human-lab/tests/test_capture.py`

**Step 1: Write the failing test**

```python
def test_mss_capture_globalizes_detection_bbox_from_roi():
    assert capture.globalize_bbox((10, 20, 30, 40)) == (roi.left + 10, roi.top + 20, roi.left + 30, roi.top + 40)
```

**Step 2: Run test to verify it fails**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_capture.py -q`
Expected: FAIL because ROI metadata and bbox globalization are missing.

**Step 3: Write minimal implementation**

Capture only the ROI rectangle, expose ROI metadata, and add bbox globalization helpers.

**Step 4: Run test to verify it passes**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_capture.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/capture/base.py src/screen_human_lab/capture/mss_capture.py tests/test_capture.py
 git commit -m "feat: capture centered roi only"
```

### Task 3: Add gated detection service

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/pipeline/gated_runtime.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`

**Step 1: Write the failing test**

```python
def test_gated_service_skips_inference_when_left_mouse_not_pressed():
    result = service.process_once(active=False)
    assert result.detections == []
```

**Step 2: Run test to verify it fails**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py -q`
Expected: FAIL because the gated runtime service does not exist.

**Step 3: Write minimal implementation**

Add a small service with deterministic `process_once()` behavior and an optional threaded loop for the overlay workflow.

**Step 4: Run test to verify it passes**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/pipeline/gated_runtime.py tests/test_gated_runtime.py
 git commit -m "feat: add gated detection runtime"
```

### Task 4: Add macOS overlay window support

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/overlay/appkit_overlay.py`
- Create: `screen-human-lab/src/screen_human_lab/overlay/state.py`
- Modify: `screen-human-lab/pyproject.toml`
- Test: `screen-human-lab/tests/test_overlay_state.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_overlay_state_clears_boxes_on_release():
    state.set_detections([...])
    state.clear_detections()
    assert state.snapshot().detections == []
```

**Step 2: Run test to verify it fails**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py tests/test_project_files.py -q`
Expected: FAIL because overlay state and Cocoa dependency notes are missing.

**Step 3: Write minimal implementation**

Add a thread-safe overlay state object and a lazy-imported AppKit overlay module for click-through ROI rendering.

**Step 4: Run test to verify it passes**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py tests/test_project_files.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay pyproject.toml tests/test_overlay_state.py tests/test_project_files.py
 git commit -m "feat: add macos overlay support"
```

### Task 5: Switch CLI to overlay-driven interactive mode

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/cli.py`
- Modify: `screen-human-lab/README.md`
- Modify: `screen-human-lab/configs/realtime_mps.yaml`
- Modify: `screen-human-lab/configs/realtime_cpu.yaml`
- Test: `screen-human-lab/tests/test_cli_runtime.py`

**Step 1: Write the failing test**

```python
def test_cli_reexecs_with_mps_fallback_and_overlay_mode():
    assert maybe_reexec_for_mps_fallback(...) is True
```

**Step 2: Run test to verify it fails**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_cli_runtime.py -q`
Expected: FAIL until the CLI routes the interactive mode through the overlay workflow.

**Step 3: Write minimal implementation**

Make normal interactive runs use the overlay path, keep `--headless` for scripted checks, and document the new ROI-plus-left-click workflow.

**Step 4: Run test to verify it passes**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_cli_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/cli.py README.md configs/realtime_mps.yaml configs/realtime_cpu.yaml tests/test_cli_runtime.py
 git commit -m "feat: switch interactive mode to roi overlay"
```

### Task 6: Final verification

**Files:**
- Modify: `screen-human-lab/docs/testing/test-plan.md`
- Test: `screen-human-lab/tests/test_roi.py`
- Test: `screen-human-lab/tests/test_capture.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`
- Test: `screen-human-lab/tests/test_overlay_state.py`
- Test: `screen-human-lab/tests/test_cli_runtime.py`

**Step 1: Write the failing test**

```python
def test_manual_verification_notes_exist_for_overlay_workflow():
    assert "left mouse" in Path("docs/testing/test-plan.md").read_text()
```

**Step 2: Run test to verify it fails**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL until the test plan documents the new manual checks.

**Step 3: Write minimal implementation**

Update the test plan and run the full unit suite plus a real one-frame headless smoke test.

**Step 4: Run test to verify it passes**

Run: `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/testing/test-plan.md tests
 git commit -m "test: verify roi overlay workflow"
```
