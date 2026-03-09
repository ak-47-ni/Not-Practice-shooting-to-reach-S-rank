# Centered ROI Overlay Gated Detection Design

**Date:** 2026-03-06

**Goal:** Replace the preview-window workflow with a monitor-centered square ROI capture pipeline that only runs detection while the left mouse button is pressed, and renders results through a transparent on-screen overlay.

## Scope

- Capture only the center square ROI of the configured monitor.
- Prefer an ROI size of `1000x1000`.
- If the monitor cannot fit `1000x1000`, fall back to the largest centered square that fits.
- Remove the OpenCV preview window from the normal interactive workflow.
- Show only a transparent overlay that draws the ROI boundary and detection boxes.
- Run capture and inference only while the left mouse button is down.
- Clear detection boxes immediately when the left mouse button is released.

## Out of Scope

- Mouse movement or input injection.
- Full-screen preview rendering.
- Complex overlay widgets or clickable controls.
- Multi-monitor overlay spanning.
- Automatic model download logic beyond the local model path already in use.

## Architecture

The revised design separates the app into three cooperating parts:

1. `ROI Capture` computes a fixed center square for the chosen monitor and grabs only that region.
2. `Gated Detection Service` runs inference only when the left mouse button is down.
3. `macOS Overlay` draws the ROI boundary and the latest detection boxes on a transparent, click-through window positioned directly over the ROI.

The overlay window covers only the ROI rectangle, not the full screen. This avoids complex coordinate conversion for the whole desktop and keeps drawing logic simple and low-overhead.

## ROI Strategy

- Input setting: `capture.roi_size`
- Effective size: `min(roi_size, monitor_width, monitor_height)`
- Position: centered within the selected monitor
- Output: a fixed ROI rectangle with absolute screen coordinates and local ROI dimensions

The capture layer should expose both the ROI frame and the ROI rectangle metadata so other components can map detection boxes correctly.

## Detection Gating

The detection loop must not run continuously.

- When left mouse button is **not pressed**:
  - no frame capture
  - no inference
  - overlay shows only the ROI outline
- When left mouse button **is pressed**:
  - capture the ROI
  - run inference
  - update the latest detection boxes
- When left mouse button is **released**:
  - stop detection work immediately
  - clear detection boxes from the overlay

This gating model minimizes unnecessary compute and matches the requested interaction model.

## Overlay Design

The overlay should be implemented as a transparent macOS window that:

- sits above the target application content
- ignores mouse events
- has no title bar or border
- is positioned exactly over the ROI region
- redraws at a lightweight UI cadence using the latest shared state

The overlay draws:

- a thin ROI rectangle at all times
- person detection boxes only while gated detection is active

No image preview should be shown.

## Performance Strategy

The main performance wins come from narrowing the capture area and gating inference, not from rewriting everything in C++.

Priority order:

1. ROI-only capture
2. inference only while left mouse is pressed
3. latest-frame-wins scheduling with no backlog
4. minimal overlay drawing
5. profile bottlenecks before introducing C++ or Objective-C++

If a hotspot remains after these changes, the most likely candidates for native optimization are:

- overlay rendering glue
- ROI crop or coordinate conversion glue

Model inference itself should remain on the current optimized runtime stack.

## Platform Notes

The current `Taichi_py` environment runs as `x86_64` on macOS. That means performance improvements should prioritize algorithmic and scheduling reductions first.

The current MPS path also requires `PYTORCH_ENABLE_MPS_FALLBACK=1` because `torchvision::nms` falls back to CPU on this machine.

## Validation Plan

- Unit tests for centered ROI computation and fallback sizing
- Unit tests for gated detection service behavior
- Unit tests for CLI re-exec and overlay-mode selection
- Manual verification that no preview window appears
- Manual verification that the overlay remains click-through
- Manual verification that holding left mouse starts detection and releasing it clears the boxes
