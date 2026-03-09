# Tracking Parameter Presets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add YAML-configurable tracker parameters and ship stable/fast preset files for both MPS and CPU backends.

**Architecture:** Introduce a new `TrackingConfig` section with compatibility defaults, parse it into `AppConfig`, and pass it into tracker construction so `TemplateMatchTracker` receives its tuning values without hard-coding them in the runtime. Keep the current baseline config files intact and add four new preset files that encode the stable/fast trade-off explicitly.

**Tech Stack:** Python 3.10+, `PyYAML`, `pytest`, existing runtime/config stack

---

### Task 1: Add tracking config parsing

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/config.py`
- Test: `screen-human-lab/tests/test_config.py`

**Step 1: Write the failing test**

```python
def test_load_config_parses_tracking_section() -> None:
    config = load_config(config_path)
    assert config.tracking.match_threshold == 0.55
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_config.py -q`
Expected: FAIL because `TrackingConfig` and `AppConfig.tracking` do not exist.

**Step 3: Write minimal implementation**

Add `TrackingConfig`, validate `match_threshold` and `search_padding`, parse the new section, and keep compatibility defaults for configs that omit it.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_config.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/config.py tests/test_config.py
 git commit -m "feat: add tracking config parsing"
```

### Task 2: Wire tracking config into runtime construction

**Files:**
- Modify: `screen-human-lab/src/screen_human_lab/cli.py`
- Modify: `screen-human-lab/src/screen_human_lab/pipeline/gated_runtime.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`
- Test: `screen-human-lab/tests/test_cli_runtime.py`

**Step 1: Write the failing test**

```python
def test_runtime_uses_configured_tracker_parameters() -> None:
    runtime = GatedDetectionRuntime(...)
    assert runtime_uses_tracker_values is True
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py tests/test_cli_runtime.py -q`
Expected: FAIL because tracker settings are still hard-coded.

**Step 3: Write minimal implementation**

Build the tracker from config-derived values and inject it into the runtime through a tracker factory.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_gated_runtime.py tests/test_cli_runtime.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/cli.py src/screen_human_lab/pipeline/gated_runtime.py tests/test_gated_runtime.py tests/test_cli_runtime.py
 git commit -m "feat: wire tracking parameters into runtime"
```

### Task 3: Add preset config files and documentation

**Files:**
- Create: `screen-human-lab/configs/realtime_mps_stable.yaml`
- Create: `screen-human-lab/configs/realtime_mps_fast.yaml`
- Create: `screen-human-lab/configs/realtime_cpu_stable.yaml`
- Create: `screen-human-lab/configs/realtime_cpu_fast.yaml`
- Modify: `screen-human-lab/README.md`
- Modify: `screen-human-lab/docs/testing/test-plan.md`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_tracking_preset_files_exist() -> None:
    assert (ROOT / "configs" / "realtime_mps_stable.yaml").exists()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL because the preset files and docs do not exist.

**Step 3: Write minimal implementation**

Add the four preset files, describe stable vs fast usage, and update the manual test plan.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add configs README.md docs/testing/test-plan.md tests/test_project_files.py
 git commit -m "docs: add tracking preset configs"
```

### Task 4: Final verification

**Files:**
- Test: `screen-human-lab/tests/test_config.py`
- Test: `screen-human-lab/tests/test_gated_runtime.py`
- Test: `screen-human-lab/tests/test_cli_runtime.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_readme_mentions_stable_and_fast_tracking_presets() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert "stable" in text
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest tests/test_project_files.py -q`
Expected: FAIL until the docs mention the preset trade-offs.

**Step 3: Write minimal implementation**

Finish docs, then run focused tests followed by the full regression suite.

**Step 4: Run test to verify it passes**

Run: `cd /Users/ljs/screen-human-lab && conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md docs/testing/test-plan.md tests
 git commit -m "test: verify tracking preset workflow"
```
