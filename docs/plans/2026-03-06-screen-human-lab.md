# Screen Human Lab Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python project skeleton for controlled-lab real-time screen capture and human detection research with interchangeable `MPS` and `CPU` inference backends.

**Architecture:** Create a small package with typed config loading, lazy backend factories, capture adapters, a single-frame processing pipeline, and a thin CLI entrypoint. Keep optional ML dependencies isolated behind backend modules so unit tests can run without installing the heavy runtime stack.

**Tech Stack:** Python 3.12, `pytest`, `PyYAML`, `numpy`, `opencv-python`, `mss`, optional `torch`, optional `onnxruntime`, optional `ultralytics`

---

### Task 1: Create project metadata and documentation

**Files:**
- Create: `screen-human-lab/README.md`
- Create: `screen-human-lab/pyproject.toml`
- Create: `screen-human-lab/.gitignore`
- Create: `screen-human-lab/configs/realtime_mps.yaml`
- Create: `screen-human-lab/configs/realtime_cpu.yaml`

**Step 1: Write the failing test**

```python
def test_package_metadata_file_exists():
    assert False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_files.py::test_package_metadata_file_exists -v`
Expected: FAIL because files do not exist yet.

**Step 3: Write minimal implementation**

Create the package metadata files, installation instructions, and two runtime config presets.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_files.py::test_package_metadata_file_exists -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md pyproject.toml .gitignore configs/realtime_mps.yaml configs/realtime_cpu.yaml
git commit -m "feat: add project metadata and configs"
```

### Task 2: Add typed config models and backend selection

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/config.py`
- Create: `screen-human-lab/src/screen_human_lab/inference/base.py`
- Create: `screen-human-lab/src/screen_human_lab/inference/factory.py`
- Test: `screen-human-lab/tests/test_config.py`
- Test: `screen-human-lab/tests/test_factory.py`

**Step 1: Write the failing test**

```python
def test_auto_backend_prefers_mps_when_available():
    assert select_runtime_backend(...) == "mps"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py tests/test_factory.py -v`
Expected: FAIL because modules do not exist.

**Step 3: Write minimal implementation**

Implement dataclass-based config loading, backend validation, and a lazy backend factory with explicit dependency errors.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py tests/test_factory.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/config.py src/screen_human_lab/inference/base.py src/screen_human_lab/inference/factory.py tests/test_config.py tests/test_factory.py
git commit -m "feat: add config and backend selection"
```

### Task 3: Add capture and runtime primitives

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/capture/base.py`
- Create: `screen-human-lab/src/screen_human_lab/capture/mss_capture.py`
- Create: `screen-human-lab/src/screen_human_lab/capture/imagegrab_capture.py`
- Create: `screen-human-lab/src/screen_human_lab/pipeline/metrics.py`
- Create: `screen-human-lab/src/screen_human_lab/pipeline/runtime.py`
- Test: `screen-human-lab/tests/test_metrics.py`
- Test: `screen-human-lab/tests/test_runtime.py`

**Step 1: Write the failing test**

```python
def test_runtime_processes_single_frame_with_fake_backend():
    assert result.frame_index == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_metrics.py tests/test_runtime.py -v`
Expected: FAIL because runtime modules do not exist.

**Step 3: Write minimal implementation**

Add a capture interface, concrete capture adapters, moving-average metrics, and a single-frame runtime processor for deterministic tests.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_metrics.py tests/test_runtime.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/capture src/screen_human_lab/pipeline/metrics.py src/screen_human_lab/pipeline/runtime.py tests/test_metrics.py tests/test_runtime.py
git commit -m "feat: add capture and runtime primitives"
```

### Task 4: Add overlay rendering and CLI

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/pipeline/overlay.py`
- Create: `screen-human-lab/src/screen_human_lab/cli.py`
- Create: `screen-human-lab/src/screen_human_lab/__init__.py`
- Test: `screen-human-lab/tests/test_overlay.py`
- Test: `screen-human-lab/tests/test_project_files.py`

**Step 1: Write the failing test**

```python
def test_overlay_preserves_frame_shape():
    assert render_overlay(...).shape == frame.shape
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_overlay.py tests/test_project_files.py -v`
Expected: FAIL because overlay and CLI are missing.

**Step 3: Write minimal implementation**

Implement overlay drawing, CLI config loading, and a documented entrypoint that can run the single-frame or live loop.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_overlay.py tests/test_project_files.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/pipeline/overlay.py src/screen_human_lab/cli.py src/screen_human_lab/__init__.py tests/test_overlay.py tests/test_project_files.py
git commit -m "feat: add overlay and cli"
```

### Task 5: Add backend stubs and final verification

**Files:**
- Create: `screen-human-lab/src/screen_human_lab/inference/torch_mps.py`
- Create: `screen-human-lab/src/screen_human_lab/inference/onnx_cpu.py`
- Modify: `screen-human-lab/README.md`
- Test: `screen-human-lab/tests/test_factory.py`

**Step 1: Write the failing test**

```python
def test_build_backend_raises_actionable_error_for_missing_optional_dependency():
    with pytest.raises(RuntimeError):
        build_backend(...)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_factory.py -v`
Expected: FAIL until backend modules expose the documented contract.

**Step 3: Write minimal implementation**

Add lazy backend implementations that import optional ML libraries only when instantiated and raise actionable setup errors.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_factory.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/screen_human_lab/inference/torch_mps.py src/screen_human_lab/inference/onnx_cpu.py README.md tests/test_factory.py
git commit -m "feat: add optional inference backends"
```
