# Adaptive Lock Stability Design

**Date:** 2026-03-09

**Goal:** Improve the single-target tracker so it feels more “locked” during high-speed motion, reducing jitter and target loss without introducing obvious trailing lag.

## Scope

- Keep the existing centered ROI workflow.
- Keep the existing single-target lock state machine.
- Improve the tracker so it predicts motion instead of searching only around the last box.
- Increase search range automatically when measured target speed rises.
- Preserve low-speed stability by keeping the default search range tight.
- Expose the new behavior through tracking config and presets.

## Out of Scope

- Replacing the whole tracker with a deep model.
- Multi-target association.
- New UI widgets.
- Automatic control or input injection.

## Problem Statement

The current template-matching tracker searches around the last known box using a fixed padding radius. That works for modest motion, but when the target moves quickly the search area can be centered too far behind the target, making the lock feel loose, laggy, or easy to lose.

A naive fix would be heavy smoothing, but that would make the box trail behind fast motion. The design must therefore improve stability without making the tracker slow to react.

## Recommended Approach

Use an adaptive lock strategy with two linked ideas:

1. **Motion prediction**
   - estimate target velocity from the last successful update
   - center the next search around the predicted position rather than the stale box position

2. **Adaptive search padding**
   - keep a small base padding at low speed for tighter lock stability
   - enlarge the effective search padding when measured target speed increases
   - cap the growth with a configurable maximum padding

This keeps the tracker tight when the scene is calm and more permissive when the target moves fast.

## Tracking Parameters

Extend the `tracking` config section with:

- `max_search_padding`
- `prediction_gain`

Existing fields remain:

- `match_threshold`
- `search_padding` (used as the base padding)

Compatibility defaults should preserve the old behavior as closely as possible:

- `max_search_padding = search_padding`
- `prediction_gain = 0.0`

That means old configs still behave like the current fixed-window tracker.

## Runtime Behavior

For each successful tracking update:

- measure the center displacement between the previous box and the matched box
- store that as the current velocity estimate

For the next frame:

- predict the next box position using `prediction_gain * velocity`
- compute dynamic padding from the base padding plus a speed-derived expansion term
- clamp the result to `max_search_padding`
- run template matching inside that predicted search region

This allows fast motion to remain responsive without forcing high noise at low speed.

## Preset Strategy

Update the stable/fast presets to reflect the adaptive lock logic.

Recommended preset direction:

- **Stable**
  - tighter base padding
  - larger maximum padding
  - stronger prediction gain
  - higher threshold
- **Fast**
  - lighter threshold
  - moderate maximum padding
  - modest prediction gain

This yields “steady at rest, aggressive when moving” behavior for the stable preset.

## Validation Plan

- Unit test that tracker still follows small translations.
- Unit test that adaptive prediction follows a faster second move that the fixed-window version would miss.
- Unit test config parsing for `max_search_padding` and `prediction_gain`.
- Update preset file tests and README notes.
- Manual verification that the stable preset feels tighter during rapid target motion.
