# L Hotkey Toggle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an `L` hotkey that enables or disables the macOS ROI detection service while preserving the existing left-mouse-button inference gate.

**Architecture:** Extend the overlay state with a service-enabled flag, extract a small pure-Python activation controller for testable gating logic, and wire the macOS overlay event loop to toggle that state on `L`. Keep ROI capture, inference backends, and the transparent overlay path unchanged except for the new enabled/disabled gate and border-color feedback.

**Tech Stack:** Python 3.10+, `pytest`, `PyObjC`/`AppKit`, existing `mss` + inference backends

---

### Task 1: Add testable hotkey gating state

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/overlay/control.py`
- Modify: `screen-human-lab/src/screen_human_lab/overlay/state.py`
- Test: `screen-human-lab/tests/test_overlay_state.py`
- Test: `screen-human-lab/tests/test_overlay_control.py`

**Step 1: Write the failing test**

```python
def test_service_toggle_flips_enabled_state() -> None:
    control = OverlayControl()
    assert control.service_enabled is True
    control.toggle_service()
    assert control.service_enabled is False
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_control.py tests/test_overlay_state.py -q`
Expected: FAIL because the controller and enabled state are not implemented.

**Step 3: Write minimal implementation**

Add a small thread-safe control object that tracks `service_enabled`, computes effective activation from service state plus left-button state, and mirrors that enabled state into `OverlayState`.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_control.py tests/test_overlay_state.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay/control.py src/screen_human_lab/overlay/state.py tests/test_overlay_control.py tests/test_overlay_state.py
 git commit -m "feat: add overlay service toggle state"
```

### Task 2: Gate the worker with service-enabled state

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/overlay/appkit_overlay.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`
- Test: `screen-human-lab/tests/test_overlay.py`

**Step 1: Write the failing test**

```python
def test_worker_stays_inactive_when_service_disabled() -> None:
    control = OverlayControl(service_enabled=False)
    assert control.compute_active(left_mouse_down=True, infer_only_while_left_mouse_down=True) is False
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay.py tests/test_gated_runtime.py -q`
Expected: FAIL because worker activation does not incorporate service state.

**Step 3: Write minimal implementation**

Route overlay tick processing through the new control object so the worker only activates when the service is enabled and the left-button gate allows it.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay.py tests/test_gated_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay/appkit_overlay.py tests/test_overlay.py tests/test_gated_runtime.py
 git commit -m "feat: gate overlay worker with service toggle"
```

### Task 3: Add the macOS `L` hotkey and visual feedback

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/overlay/appkit_overlay.py`
- Modify: `screen-human-lab/README.md`
- Modify: `screen-human-lab/docs/testing/test-plan.md`
- Test: `screen-human-lab/tests/test_project_files.py`
- Test: `screen-human-lab/tests/test_cli_runtime.py`

**Step 1: Write the failing test**

```python
def test_readme_mentions_l_hotkey_toggle() -> None:
    assert "press `L`" in Path("README.md").read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py tests/test_cli_runtime.py -q`
Expected: FAIL because docs and overlay behavior do not yet mention the new toggle.

**Step 3: Write minimal implementation**

Install an AppKit key monitor for `L`, toggle the service state, color the ROI border by enabled state, and document the manual interaction model.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py tests/test_cli_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay/appkit_overlay.py README.md docs/testing/test-plan.md tests/test_project_files.py tests/test_cli_runtime.py
 git commit -m "feat: add l hotkey toggle for overlay mode"
```

### Task 4: Final verification

**Files:**
- Test: `screen-human-lab/tests/test_overlay_control.py`
- Test: `screen-human-lab/tests/test_overlay_state.py`
- Test: `screen-human-lab/tests/test_overlay.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_manual_test_plan_mentions_hotkey_toggle() -> None:
    assert "press L" in Path("docs/testing/test-plan.md").read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL until the manual test notes include the hotkey workflow.

**Step 3: Write minimal implementation**

Finish docs, run the focused tests, then run the full suite for regression coverage.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/testing/test-plan.md tests
 git commit -m "test: verify l hotkey overlay workflow"
```
