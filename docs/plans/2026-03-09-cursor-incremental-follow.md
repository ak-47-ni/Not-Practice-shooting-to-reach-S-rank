# Cursor Incremental Follow Implementation Plan

> Superseded in part by `docs/plans/2026-03-09-half-roi-detection.md` for the final ROI-sizing decision.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the mouse toward the normalized locked detection center while the left mouse button is held, with ROI-center fallback when cursor reads fail.

**Architecture:** Keep the detector/tracker bbox at true size, map the locked target center into Quartz coordinates with monitor-aware scaling, and move the cursor along a straight-line path from the current cursor position or the ROI-center fallback. Expose speed and minimum stop distance through overlay config so the runtime can be tuned without editing code.

**Tech Stack:** Python 3.10+, `pytest`, `PyObjC`/`AppKit`, existing overlay state and gated runtime stack

---

### Task 1: Add cursor-step helpers and tests

**Files:**
- Modify: `src/screen_human_lab/overlay/state.py`
- Modify: `tests/test_overlay_state.py`

**Step 1: Write the failing test**

```python
def test_compute_cursor_delta_preserves_dxdy_signs() -> None:
    assert compute_cursor_delta(dx=120, dy=-80) == (expected_x, expected_y)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py -q`
Expected: FAIL because the cursor-step helper does not yet exist.

**Step 3: Write minimal implementation**

Add a pure helper that converts signed `dx/dy` into bounded per-tick cursor steps with deadzone and clamp handling.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay/state.py tests/test_overlay_state.py
git commit -m "feat: add cursor delta helpers"
```

### Task 2: Add macOS cursor-follow controller

**Files:**
- Modify: `src/screen_human_lab/overlay/appkit_overlay.py`
- Modify: `tests/test_overlay_control.py`

**Step 1: Write the failing test**

```python
def test_cursor_follow_moves_when_snapshot_has_detection() -> None:
    controller = CursorFollowController(...)
    controller.update(...)
    assert mover.moves == [(expected_dx, expected_dy)]
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_control.py -q`
Expected: FAIL because the cursor-follow controller does not yet exist.

**Step 3: Write minimal implementation**

Add a macOS cursor mover plus a small controller that reads the latest overlay snapshot and applies bounded incremental movement only while active.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_control.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay/appkit_overlay.py tests/test_overlay_control.py
git commit -m "feat: add overlay cursor follow controller"
```

### Task 3: Verify gated behavior still holds

**Files:**
- Test: `tests/test_gated_runtime.py`
- Test: `tests/test_overlay_state.py`
- Test: `tests/test_overlay_control.py`

**Step 1: Write the failing test**

```python
def test_cursor_follow_stops_when_snapshot_has_no_detection() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py tests/test_overlay_control.py -q`
Expected: FAIL until the inactive and no-detection cases are handled.

**Step 3: Write minimal implementation**

Finish the controller guards and keep the existing gated-runtime behavior unchanged.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py tests/test_overlay_control.py tests/test_gated_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests
git commit -m "test: verify overlay cursor follow gating"
```
