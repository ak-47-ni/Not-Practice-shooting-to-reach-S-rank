# Test Plan

## Summary

- Feature/Change: Centered ROI capture, transparent overlay, right mouse gated detection, `L` hotkey service toggle, single target lock with re-detect after more than 5 lost frames, adaptive lock tracking presets, dx/dy overlay readout, and a Windows-first preview stability pipeline
- Module/Area: Config, ROI geometry, capture cropping, gated runtime, overlay state, CLI workflow
- Scope: Unit tests for geometry, stability, and scheduling plus manual smoke checks for the Windows preview workflow and the macOS overlay workflow

## Test Mapping (1:1)

| Code Change | File/Function | Test Change | Test File |
| --- | --- | --- | --- |
| Add centered ROI geometry | `src/screen_human_lab/roi.py` | Validate centered square sizing and fallback | `tests/test_roi.py` |
| Add ROI-aware capture metadata | `src/screen_human_lab/capture/mss_capture.py` | Validate bbox globalization and monitor error handling | `tests/test_capture.py` |
| Add gated inference runtime | `src/screen_human_lab/pipeline/gated_runtime.py` | Validate single-target lock, 5 lost frames retention, and re-detect behavior | `tests/test_gated_runtime.py` |
| Add template tracker | `src/screen_human_lab/tracking/template_match.py` | Validate translated target tracking and disappearance failure | `tests/test_template_tracker.py` |
| Add overlay state container | `src/screen_human_lab/overlay/state.py` | Validate clear-on-release behavior, service enabled state, and dx/dy offset helpers | `tests/test_overlay_state.py` |
| Add overlay control logic | `src/screen_human_lab/overlay/control.py` | Validate `L` hotkey matching and service activation rules | `tests/test_overlay_control.py` |
| Extend config and packaging | `src/screen_human_lab/config.py`, `pyproject.toml` | Validate ROI fields, CUDA auto-selection, and Cocoa dependency declaration | `tests/test_config.py`, `tests/test_project_files.py` |
| Add stability helpers | `src/screen_human_lab/pipeline/global_motion.py`, `src/screen_human_lab/pipeline/target_scoring.py`, `src/screen_human_lab/pipeline/lock_state.py`, `src/screen_human_lab/pipeline/target_filter.py` | Validate motion compensation, scoring, state transitions, and smoothing | `tests/test_global_motion.py`, `tests/test_target_scoring.py`, `tests/test_lock_state.py`, `tests/test_target_filter.py` |
| Add Windows preview runtime | `src/screen_human_lab/pipeline/runtime.py`, `src/screen_human_lab/cli.py` | Validate local stabilized detections for preview sessions | `tests/test_preview_runtime.py`, `tests/test_cli_runtime.py` |
| Switch interactive workflow | `src/screen_human_lab/cli.py` | Validate fallback re-exec, overlay workflow selection, and tracker factory wiring | `tests/test_cli_runtime.py` |

## Test Cases

- Happy path
  - Load valid config with `roi_size` and overlay mode.
  - Compute centered ROI for a monitor that can fit the requested size.
  - Hold right mouse state active and verify detection boxes are mapped to global coordinates.
  - Confirm that only one single target is shown during a continuous right-mouse hold.
- Edge cases
  - Monitor smaller than the requested `1000x1000` ROI.
  - Missing monitor metadata.
  - Right mouse not pressed, so inference should be skipped.
- Error cases
  - Missing config file.
  - Invalid overlay mode.
  - Missing optional Cocoa dependency when interactive overlay mode starts.

## Test Execution

- Command(s): `conda run -p /Users/ljs/conda/envs/Taichi_py python -m pytest -q`
- Environment: local macOS development environment
- Data fixtures: synthetic numpy frames, fake capture, fake backend, fake overlay state
- Expected duration: under 5 seconds for unit tests

## Manual Checks

- Compare the adaptive `stable` and `fast` tracking presets on the same screen content and confirm the expected trade-off between steadiness and responsiveness.
- Hold the right mouse button to start detection, then hold the left mouse button as well and verify the cursor follows the locked target.
- Verify that the overlay top-right corner shows `dx/dy` only while a target is locked.
- Start the interactive mode and verify that no preview window appears.
- Verify that the transparent overlay shows the ROI boundary.
- press `L` and verify that the ROI border changes state while remaining visible.
- With the service disabled, hold the right mouse button and verify that no detection boxes appear.
- press `L` again to re-enable detection.
- Hold the right mouse button and verify that only one single target box appears even if multiple people are visible.
- Briefly hide the locked target and verify that the previous lock is retained for up to 5 lost frames.
- Keep the target lost longer and verify that the runtime re-detects after more than 5 lost frames.
- Release the right mouse button and verify that detection boxes clear immediately.
- Verify that the overlay remains click-through during normal app usage.

## Risks

- Known flakiness: overlay manual checks depend on active desktop session and screen recording permission
- External dependencies: optional Cocoa runtime packages are required for the interactive overlay path
- Follow-up work: add end-to-end overlay smoke coverage if a stable UI test harness is introduced
