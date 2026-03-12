# Windows Stability Preview Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Windows-first preview workflow with CUDA-first backend selection and a stability pipeline for smoother, more reliable target locking.

**Architecture:** Extend the existing detector/tracker prototype with a dedicated stability layer: global motion estimation, multi-factor candidate scoring, lock-state management, and filtered output. Keep the preview path simple and Windows-friendly while preserving the current macOS overlay as a secondary branch.

**Tech Stack:** Python, pytest, OpenCV, NumPy, PyYAML, MSS, Ultralytics YOLO, PyTorch/CUDA

---

### Task 1: Add Windows-first config and backend tests

**Files:**
- Modify: `tests/test_config.py`
- Modify: `tests/test_factory.py`
- Modify: `tests/test_cli_runtime.py`
- Modify: `tests/test_project_files.py`

**Step 1: Write the failing tests**
- Add tests for `auto -> cuda` backend selection.
- Add tests for `stability` config parsing and defaults.
- Add tests for Windows preview config files and CUDA preference.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py tests/test_factory.py tests/test_cli_runtime.py tests/test_project_files.py -q`
Expected: FAIL because CUDA and stability support do not exist yet.

**Step 3: Write minimal implementation**
- Update `src/screen_human_lab/config.py` to support `cuda` and `stability`.
- Update `src/screen_human_lab/inference/factory.py` and add `src/screen_human_lab/inference/torch_cuda.py`.
- Add Windows preview config files under `configs/`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py tests/test_factory.py tests/test_cli_runtime.py tests/test_project_files.py -q`
Expected: PASS.

### Task 2: Add stability pipeline unit tests

**Files:**
- Create: `tests/test_global_motion.py`
- Create: `tests/test_target_scoring.py`
- Create: `tests/test_lock_state.py`
- Create: `tests/test_target_filter.py`
- Modify: `tests/test_template_tracker.py`

**Step 1: Write the failing tests**
- Add deterministic unit tests for motion estimation, scoring, lock-state transitions, smoothing, and template tracking motion hints.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_global_motion.py tests/test_target_scoring.py tests/test_lock_state.py tests/test_target_filter.py tests/test_template_tracker.py -q`
Expected: FAIL because the new modules and tracker API do not exist yet.

**Step 3: Write minimal implementation**
- Create `src/screen_human_lab/pipeline/global_motion.py`.
- Create `src/screen_human_lab/pipeline/target_scoring.py`.
- Create `src/screen_human_lab/pipeline/lock_state.py`.
- Create `src/screen_human_lab/pipeline/target_filter.py`.
- Extend `src/screen_human_lab/tracking/template_match.py` with optional motion hints.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_global_motion.py tests/test_target_scoring.py tests/test_lock_state.py tests/test_target_filter.py tests/test_template_tracker.py -q`
Expected: PASS.

### Task 3: Integrate stability into the runtime

**Files:**
- Modify: `src/screen_human_lab/pipeline/gated_runtime.py`
- Modify: `src/screen_human_lab/pipeline/runtime.py`
- Modify: `src/screen_human_lab/pipeline/overlay.py`
- Modify: `tests/test_gated_runtime.py`
- Create: `tests/test_preview_runtime.py`

**Step 1: Write the failing tests**
- Add runtime tests for stable target retention, smoothed output, and preview-session rendering from local detections.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_gated_runtime.py tests/test_preview_runtime.py tests/test_runtime.py -q`
Expected: FAIL because the runtime is not yet wired to the stability modules.

**Step 3: Write minimal implementation**
- Refactor `GatedDetectionRuntime` into the main stability coordinator.
- Add a preview runtime class for the Windows-first local-coordinate path.
- Extend overlay rendering to show status text and optional debug lines.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_gated_runtime.py tests/test_preview_runtime.py tests/test_runtime.py -q`
Expected: PASS.

### Task 4: Wire the CLI and documentation

**Files:**
- Modify: `src/screen_human_lab/cli.py`
- Modify: `README.md`
- Modify: `docs/testing/test-plan.md`

**Step 1: Write the failing tests**
- Extend CLI and project-file tests for Windows preview guidance.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_runtime.py tests/test_project_files.py -q`
Expected: FAIL until the docs and CLI reflect the new Windows-first preview path.

**Step 3: Write minimal implementation**
- Make the preview path the preferred documented workflow for Windows.
- Keep the macOS overlay path as secondary documentation.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_runtime.py tests/test_project_files.py -q`
Expected: PASS.

### Task 5: Verify the refactor end-to-end

**Files:**
- Modify: `src/screen_human_lab/pipeline/__init__.py`

**Step 1: Run the focused verification suite**

Run: `pytest tests/test_config.py tests/test_factory.py tests/test_cli_runtime.py tests/test_project_files.py tests/test_global_motion.py tests/test_target_scoring.py tests/test_lock_state.py tests/test_target_filter.py tests/test_template_tracker.py tests/test_gated_runtime.py tests/test_preview_runtime.py tests/test_runtime.py -q`
Expected: PASS.

**Step 2: Run the full project test suite**

Run: `pytest -q`
Expected: PASS.

