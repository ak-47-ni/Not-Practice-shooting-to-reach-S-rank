# DX DY Overlay Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Display the locked target's real-time `dx/dy` offset from screen center in the overlay's top-right corner.

**Architecture:** Add a small pure helper for offset calculation and string formatting, reuse the current single-target detection state as the source of truth, and extend the AppKit overlay to draw a fixed-position label without changing the capture or inference pipeline.

**Tech Stack:** Python 3.10+, `pytest`, `PyObjC`/`AppKit`, existing overlay and runtime stack

---

### Task 1: Add offset helper and tests

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/overlay/state.py`
- Modify: `screen-human-lab/tests/test_overlay_state.py`

**Step 1: Write the failing test**

```python
def test_compute_detection_offset_uses_screen_coordinate_signs() -> None:
    offset = compute_detection_offset(...)
    assert offset.dx > 0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py -q`
Expected: FAIL because the helper does not yet exist.

**Step 3: Write minimal implementation**

Add a compact helper that computes integer pixel offsets and formats them as `dx=...  dy=...`.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_overlay_state.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay/state.py tests/test_overlay_state.py
 git commit -m "feat: add overlay offset helpers"
```

### Task 2: Draw offset text in the AppKit overlay

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/overlay/appkit_overlay.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_readme_mentions_dx_dy_overlay() -> None:
    assert "dx" in Path("README.md").read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL because the docs do not yet mention the new readout.

**Step 3: Write minimal implementation**

Draw a fixed-position label in the overlay top-right corner using the first locked detection as the offset source.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/overlay/appkit_overlay.py README.md docs/testing/test-plan.md tests/test_project_files.py
 git commit -m "feat: draw dx dy overlay readout"
```

### Task 3: Final verification

**Files:**
- Test: `screen-human-lab/tests/test_overlay_state.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_test_plan_mentions_dx_dy_overlay() -> None:
    assert "dx/dy" in Path("docs/testing/test-plan.md").read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL until docs mention the readout.

**Step 3: Write minimal implementation**

Finish docs and run focused tests plus full regression coverage.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md docs/testing/test-plan.md tests
 git commit -m "test: verify dx dy overlay workflow"
```
