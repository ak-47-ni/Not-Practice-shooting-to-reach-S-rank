# DX DY Overlay Design

**Date:** 2026-03-09

**Goal:** Show the locked target's real-time offset from the screen center as `dx/dy` text in the overlay's top-right corner, using screen-coordinate semantics where `+dx` points right and `+dy` points down.

## Scope

- Keep the existing centered ROI workflow.
- Keep the existing single-target lock behavior.
- Compute offset from the selected monitor's center point.
- Show the offset in the overlay's top-right corner.
- Use `+dx` for right and `+dy` for down.
- Only show offset text while a locked target is currently available.

## Out of Scope

- Mouse movement or cursor control.
- New windows or preview panes.
- Crosshair lines or arrows.
- Logging offsets to disk.

## Offset Definition

The current overlay window covers the centered ROI, and that ROI is centered on the selected monitor. Because of that, the ROI center is the same as the target monitor's center for the purposes of this feature.

Definitions:

- `screen_center_x = roi_rect.left + roi_rect.width / 2`
- `screen_center_y = roi_rect.top + roi_rect.height / 2`
- `target_center_x = (bbox.x1 + bbox.x2) / 2`
- `target_center_y = (bbox.y1 + bbox.y2) / 2`
- `dx = target_center_x - screen_center_x`
- `dy = target_center_y - screen_center_y`

The displayed values should be rounded to integer pixels.

## Display Behavior

- When there is no active locked target, do not draw `dx/dy` text.
- When there is a locked target, draw one compact label in the overlay's top-right corner.
- Example text:
  - `dx=+42  dy=-18`
  - `dx=-75  dy=+33`

The text should stay visually stable by using a fixed anchor position rather than following the box.

## UI Style

Recommended style:

- small monospace-like or compact system font
- light text color
- semi-transparent dark background capsule or rectangle
- modest padding from the overlay edge, around `10-12px`

This keeps the data legible without overwhelming the ROI overlay.

## Implementation Strategy

The simplest implementation path is to keep the current overlay state unchanged and compute the offset directly from the current detection box plus `roi_rect` when drawing.

To keep the behavior testable, add a small pure-Python helper that:

- computes integer `dx/dy` from `roi_rect` and one detection
- formats the display string

The AppKit overlay then only handles drawing.

## Validation Plan

- Unit test the offset helper with detections in each quadrant.
- Unit test string formatting for sign handling.
- Update docs/tests to mention the overlay `dx/dy` readout.
- Manual verification that the label appears in the overlay top-right corner only when a target is present.
