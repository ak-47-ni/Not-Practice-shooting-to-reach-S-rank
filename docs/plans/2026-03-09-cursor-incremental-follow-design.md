# Cursor Incremental Follow Design

> Superseded in part by `docs/plans/2026-03-09-half-roi-detection-design.md` for the final ROI-sizing decision.

**Date:** 2026-03-09

**Goal:** When the left mouse button is held and a target is locked, move the mouse continuously toward the locked target center along a straight-line path, with ROI-center fallback when the current cursor position cannot be read.

## Scope

- Keep the existing centered ROI workflow.
- Keep the existing single-target lock behavior.
- Reuse the existing `dx/dy` sign convention where `+dx` points right and `+dy` points down.
- Keep the selected detection box at its true size; later ROI sizing changes are documented in the dedicated half-ROI design.
- Only move the mouse while the service is enabled, the left mouse button is held, and a locked target is available.
- Apply mouse motion as incremental updates rather than snapping directly to the detection center.

## Out of Scope

- New automation modes outside the current left-mouse gate.
- Input injection for keyboard or mouse clicks.
- Changing the current target-selection strategy.
- New configuration UI.

## Behavior Definition

The current overlay state already exposes the ROI rectangle and the globally mapped locked detection box. The cursor-follow feature should reuse that state, but the movement vector must be based on the current cursor position and the locked target center rather than the ROI center.

Definitions:

- `dx = target_center_x - roi_center_x`
- `dy = target_center_y - roi_center_y`
- `cursor_delta_x = target_center_x - current_cursor_x`
- `cursor_delta_y = target_center_y - current_cursor_y`

The sign convention must stay screen-oriented:

- `+dx`: move right
- `-dx`: move left
- `+dy`: move down
- `-dy`: move up

Because Quartz mouse coordinates and screen-capture coordinates can differ in both origin and scale, the runtime mouse-update path must map screen-space target centers into Quartz coordinates using the active monitor and screen geometry.

## Recommended Approach

Use the AppKit overlay timer loop as the control point for cursor motion.

1. Keep detection and tracking inside the existing gated worker thread.
2. Convert the locked target center into Quartz coordinates with monitor-aware scale correction.
3. Read the current mouse position; if that fails, fall back to the ROI center in Quartz coordinates.
4. Convert the cursor-to-target vector into a straight-line movement step using speed and minimum-distance settings.
5. Apply the resulting absolute target cursor position only when the current session is active.

This keeps inference and cursor movement loosely coupled and makes the step calculation easy to unit test.

## Step Strategy

Use a small pure helper that converts the current cursor-to-target vector into a distance-limited straight-line step:

- compute the Euclidean remaining distance
- stop once the remaining distance is within `min_distance`
- otherwise move by `speed_pixels_per_second * delta_time`
- if the remaining distance is smaller than one step, snap directly to the normalized target center

This gives fast updates while preserving a straight-line approach to the current target.

## Validation Plan

- Unit test the movement-step helper for straight-line scaling and stop distance.
- Unit test the cursor-follow controller so it falls back to the ROI center when the current cursor position cannot be read.
- Unit test the target-point conversion with monitor-to-screen scaling.
- Unit test the runtime so the locked box keeps its true size while cursor-follow consumes the correct center point.
- Run focused overlay tests plus the existing gated-runtime tests.
