# L Hotkey Toggle Design

**Date:** 2026-03-06

**Goal:** Add a lightweight keyboard toggle so pressing `L` enables or disables the existing ROI-gated person-detection service without restoring the preview window.

## Scope

- Add a macOS interactive hotkey toggle bound to `L`.
- Keep the existing centered `1000x1000` ROI capture behavior.
- Keep the existing left-mouse-button gate for capture and inference.
- Make the effective detection condition `service_enabled && left_mouse_down`.
- When disabled, skip capture and inference entirely.
- When disabled, keep the ROI border visible but suppress detection boxes.
- Provide a lightweight visual state cue through ROI border color.

## Out of Scope

- Any mouse movement or input injection.
- Reintroducing an OpenCV preview window.
- Clickable overlay widgets or floating toolbars.
- Cross-platform global hotkey support outside the current macOS overlay path.
- Rebinding hotkeys from the UI.

## Behavior Summary

The overlay continues to run as a transparent click-through window over the ROI. Pressing `L` flips a global service state:

- **Enabled:** detection is allowed, but still only runs while the left mouse button is down.
- **Disabled:** detection never runs, regardless of mouse state.

This keeps the current low-overhead gating model while adding an explicit operator-controlled pause switch.

## Architecture

The change adds a small service-state layer to the existing overlay-driven workflow:

1. `Hotkey Listener` captures the `L` key inside the macOS overlay event loop.
2. `Overlay State` stores whether the service is enabled and exposes that state to rendering.
3. `Detection Worker` combines the hotkey state with the existing left-button gate before calling the runtime.
4. `Overlay View` always draws the ROI border, but changes border color based on the enabled state and only draws detection boxes when detection is active.

The hotkey handling should stay in the overlay module so the rest of the pipeline remains UI-agnostic.

## State Model

The runtime now has two gates:

- `service_enabled`: toggled by `L`
- `left_mouse_down`: sampled from the current mouse state

Effective activation rule:

`active = service_enabled and (left_mouse_down if left-click-gating is enabled else True)`

State transitions should clear stale detections whenever the service is disabled so the overlay immediately reflects the paused state.

## UI Feedback

The overlay should keep feedback intentionally minimal:

- ROI border is always visible.
- ROI border is **green** when the service is enabled.
- ROI border is **gray** when the service is disabled.
- Detection boxes are only visible when the runtime is actively processing frames.

No text badge or status HUD is required for this change.

## Error Handling

- If macOS keyboard monitoring requires unavailable functionality, the app should fail with a clear startup error rather than silently behaving unpredictably.
- If the event monitor cannot be installed, interactive overlay mode should stop cleanly.
- Toggling the service must be thread-safe and must not crash if the key is pressed rapidly.

## Performance Notes

This change should preserve the current performance wins:

- no inference unless both gates allow it
- no unnecessary capture when disabled
- no extra preview window rendering
- only lightweight overlay redraw work at UI cadence

The implementation should stay in Python/AppKit unless profiling later shows the hotkey path or overlay rendering to be a real bottleneck.

## Validation Plan

- Unit test hotkey/service state transitions in a UI-free helper.
- Unit test worker activation logic for `service_enabled` plus left-button gating.
- Unit test overlay snapshot state for enabled/disabled transitions.
- Unit test config or defaults only if a new config surface is introduced.
- Manual verification that pressing `L` toggles between green and gray ROI borders.
- Manual verification that disabled mode skips detection even while holding the left mouse button.
