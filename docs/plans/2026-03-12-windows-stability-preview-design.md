# Windows Stability Preview Design

**Date:** 2026-03-12

**Goal:** Rework the project into a Windows-first preview workflow that prioritizes stable target selection, lock retention, and smooth display output before introducing any training stack.

## Scope

- Make Windows the primary runtime target.
- Prioritize standard preview windows over the existing macOS-only transparent overlay path.
- Add a CUDA-first inference route for NVIDIA GPUs, with CPU fallback.
- Strengthen non-training stability through motion compensation, multi-factor scoring, lock state management, and smoothed output.
- Preserve the existing research prototype structure where practical so future training hooks can reuse the runtime state.

## Architecture

The first phase keeps the lightweight ROI capture and pretrained person detector, but moves final target selection out of the detector and into a Windows-friendly stability pipeline. The runtime becomes a coordinator that combines detector output, tracker output, motion compensation, lock-state decisions, and smoothed display state.

The resulting system has four layers:

1. **Platform Layer**: Windows-first ROI capture and preview window flow.
2. **Perception Layer**: detector backends plus global motion estimation.
3. **Locking Layer**: candidate scoring, lock state machine, and tracker integration.
4. **Presentation Layer**: preview rendering of the filtered target state and debug status.

## Platform Strategy

- Windows is the preferred runtime target.
- The ordinary preview window is the primary interactive mode.
- The macOS AppKit overlay remains available only as a secondary path.
- System cursor control is deferred to a later phase.

## Detection and Locking Strategy

The existing “nearest box to center” rule is replaced with a multi-factor scorer that balances:

- detector confidence
- distance to the predicted target position
- overlap with the prior lock
- size continuity against the current lock

Lock handling becomes stateful instead of purely frame-local. The runtime distinguishes between acquiring, locked, and recovering phases so it can resist spurious target switches during fast motion or brief visual loss.

## Stability Strategy

Stability improves through four coordinated components:

1. **Global Motion Estimation** to separate camera shake from object motion.
2. **Template Tracking with Motion Hints** to keep local continuity during large frame translations.
3. **Lock State Management** to avoid instant relock or target switching.
4. **Target Filtering** to smooth display boxes and derived offsets.

## Windows Runtime Path

The Windows path uses a standard preview window and a CUDA-first backend selection flow. The CLI should prefer a preview session that renders stabilized detections, while the current macOS overlay route should continue to work only as a non-primary platform branch.

## Configuration Changes

Add a dedicated `stability` section to the application config so the runtime can tune motion compensation, scoring behavior, loss tolerance, and smoothing without overloading the tracking settings.

Expected config areas:

- `capture`
- `inference`
- `overlay`
- `tracking`
- `stability`

## Testing Strategy

The first phase should be test-driven and focus on deterministic unit coverage rather than UI automation.

Required test areas:

- CUDA auto-selection and Windows preview defaults
- stability config parsing and defaults
- motion estimation on translated frames
- scoring behavior when lock continuity conflicts with center distance
- lock-state transitions through acquisition, loss, recovery, and reset
- smoothing behavior for jittery boxes
- gated runtime integration with the stability pipeline
- preview runtime integration on the local coordinate path

## Deferred Work

- Windows transparent overlay and click-through UI
- system cursor following on Windows
- segmentation refinement
- manual training data collection and learned policies

