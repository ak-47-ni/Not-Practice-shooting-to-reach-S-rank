# Adaptive Lock Stability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the single-target tracker more stable during fast motion by combining motion prediction with adaptive search padding.

**Architecture:** Extend `TemplateMatchTracker` with internal velocity state, a predicted search center, and a speed-based padding expansion that is capped by config. Parse the new fields through `TrackingConfig`, wire them through the tracker factory, and update stable/fast presets to take advantage of the new adaptive lock behavior.

**Tech Stack:** Python 3.10+, `numpy`, `opencv-python`, `PyYAML`, `pytest`

---

### Task 1: Add adaptive tracker tests

**Files:**
- Modify: `screen-human-lab/tests/test_template_tracker.py`

**Step 1: Write the failing test**

```python
def test_template_tracker_uses_motion_prediction_for_faster_second_move() -> None:
    tracker = TemplateMatchTracker(...)
    assert tracker.update(frame2).success is True
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_template_tracker.py -q`
Expected: FAIL because the tracker still uses a fixed search window.

**Step 3: Write minimal implementation**

Add velocity estimation, predicted search center, and adaptive padding.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_template_tracker.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/tracking/template_match.py tests/test_template_tracker.py
 git commit -m "feat: add adaptive lock tracking"
```

### Task 2: Parse and wire new tracking config

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/config.py`
- Modify: `screen-human-lab/src/screen_human_lab/cli.py`
- Modify: `screen-human-lab/tests/test_config.py`
- Modify: `screen-human-lab/tests/test_cli_runtime.py`

**Step 1: Write the failing test**

```python
def test_load_config_parses_adaptive_tracking_fields() -> None:
    assert config.tracking.max_search_padding == 96
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_config.py tests/test_cli_runtime.py -q`
Expected: FAIL because the new fields do not exist.

**Step 3: Write minimal implementation**

Add the new fields with compatibility defaults and pass them through the tracker factory.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_config.py tests/test_cli_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/config.py src/screen_human_lab/cli.py tests/test_config.py tests/test_cli_runtime.py
 git commit -m "feat: wire adaptive tracking config"
```

### Task 3: Update presets and docs

**Files:**
- Modify: `screen-human-lab/configs/realtime_mps_stable.yaml`
- Modify: `screen-human-lab/configs/realtime_mps_fast.yaml`
- Modify: `screen-human-lab/configs/realtime_cpu_stable.yaml`
- Modify: `screen-human-lab/configs/realtime_cpu_fast.yaml`
- Modify: `screen-human-lab/README.md`
- Modify: `screen-human-lab/docs/testing/test-plan.md`
- Modify: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_tracking_presets_include_adaptive_lock_fields() -> None:
    assert "prediction_gain" in preset_text
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL because the preset files and docs do not yet mention adaptive lock.

**Step 3: Write minimal implementation**

Add the new preset fields and document the stronger-lock behavior.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add configs README.md docs/testing/test-plan.md tests/test_project_files.py
 git commit -m "docs: add adaptive lock presets"
```

### Task 4: Final verification

**Files:**
- Test: `screen-human-lab/tests/test_template_tracker.py`
- Test: `screen-human-lab/tests/test_config.py`
- Test: `screen-human-lab/tests/test_cli_runtime.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_readme_mentions_adaptive_lock_behavior() -> None:
    assert "adaptive" in Path("README.md").read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL until the docs mention the stronger-lock behavior.

**Step 3: Write minimal implementation**

Finish docs, run focused tests, then run the full suite.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md docs/testing/test-plan.md tests
 git commit -m "test: verify adaptive lock workflow"
```
