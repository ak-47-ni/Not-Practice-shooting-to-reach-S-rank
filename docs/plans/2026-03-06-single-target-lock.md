# Single Target Lock Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a single-target lock workflow that detects one person per left-mouse hold, tracks only that person, tolerates up to 5 lost frames, and then re-detects.

**Architecture:** Extend the gated runtime with a small lock state machine, inject a lightweight template-matching tracker built from standard OpenCV functions, and keep the overlay unchanged except that it now receives at most one detection at a time. Reset all lock state whenever the runtime becomes inactive.

**Tech Stack:** Python 3.10+, `numpy`, `opencv-python`, `pytest`, existing ROI capture and inference backends

---

### Task 1: Add tracker primitives and tests

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/tracking/template_match.py`
- Create: `screen-human-lab/src/screen_human_lab/tracking/__init__.py`
- Test: `screen-human-lab/tests/test_template_tracker.py`

**Step 1: Write the failing test**

```python
def test_template_tracker_updates_bbox_for_translated_patch() -> None:
    tracker = TemplateMatchTracker()
    tracker.initialize(frame0, (20, 20, 40, 40))
    result = tracker.update(frame1)
    assert result.success is True
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_template_tracker.py -q`
Expected: FAIL because the tracker module does not exist.

**Step 3: Write minimal implementation**

Implement a template-matching tracker that stores a grayscale template, searches near the previous box, and returns success plus an updated bbox.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_template_tracker.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/tracking tests/test_template_tracker.py
 git commit -m "feat: add template tracker"
```

### Task 2: Add runtime target-lock state machine

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/pipeline/gated_runtime.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`

**Step 1: Write the failing test**

```python
def test_runtime_selects_single_target_closest_to_roi_center() -> None:
    result = runtime.process_once(active=True)
    assert len(result.detections) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py -q`
Expected: FAIL because the runtime still returns all detections and has no lock state.

**Step 3: Write minimal implementation**

Add a lock state, choose the center-nearest detection, initialize the tracker, preserve the last bbox for 5 failed tracking frames, and re-detect on the 6th failed frame.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/pipeline/gated_runtime.py tests/test_gated_runtime.py
 git commit -m "feat: add single target lock runtime"
```

### Task 3: Document the single-target workflow

**Files:**
- Modify: `screen-human-lab/README.md`
- Modify: `screen-human-lab/docs/testing/test-plan.md`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_readme_mentions_single_target_lock_and_5_frame_recovery() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert "single target" in text
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL because the docs do not yet describe the target-lock workflow.

**Step 3: Write minimal implementation**

Document that each left-mouse hold locks at most one target, tracks only that target, and re-detects after more than 5 lost frames.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md docs/testing/test-plan.md tests/test_project_files.py
 git commit -m "docs: describe single target lock workflow"
```

### Task 4: Final verification

**Files:**
- Test: `screen-human-lab/tests/test_template_tracker.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_manual_test_plan_mentions_re_detect_after_5_lost_frames() -> None:
    text = Path("docs/testing/test-plan.md").read_text(encoding="utf-8")
    assert "5" in text
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL until the manual verification notes mention the lost-frame threshold.

**Step 3: Write minimal implementation**

Update docs, run focused tests, then run the full suite for regression coverage.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/testing/test-plan.md tests
 git commit -m "test: verify single target lock workflow"
```
