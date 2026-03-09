# Single Target Lock Design

**Date:** 2026-03-06

**Goal:** Change the current ROI-gated person-detection workflow so each left-mouse hold locks onto at most one person, keeps tracking only that person, tolerates up to 5 lost frames, and only falls back to re-detection after the loss threshold is exceeded.

## Scope

- Keep the existing centered `1000x1000` ROI capture behavior.
- Keep the existing `L` hotkey service toggle.
- Keep the existing left-mouse gate for active processing.
- On a fresh active press, detect people within the ROI and select exactly one target.
- If multiple people are detected, choose the one whose bounding-box center is closest to the ROI center.
- After the target is selected, stop full-frame multi-person detection and track only that target.
- When tracking fails, keep the lock for up to 5 consecutive frames.
- After more than 5 consecutive lost frames, return to detection mode and search again.
- Draw at most one detection box at any time.

## Out of Scope

- Training any new model.
- Multi-target tracking.
- Identity-preserving re-identification across separate mouse presses.
- Cross-platform overlay rewrites.
- Deep GPU tracker integration.

## Behavior Summary

The active workflow becomes a small state machine:

1. **Idle**: left mouse not pressed or service disabled. No target, no tracking, no detection boxes.
2. **Detecting**: left mouse is pressed and there is no current lock. Run person detection on the ROI.
3. **Locked**: choose the single detection nearest the ROI center and initialize a tracker from that box.
4. **Tracking**: while the tracker succeeds, update only that box and ignore all other content.
5. **Temporarily Lost**: if tracking fails, keep the last locked box and continue trying to recover for up to 5 frames.
6. **Re-detect**: if tracking has failed for more than 5 consecutive frames, clear the lock and run detection again.

Releasing the left mouse button clears all lock state immediately. Pressing `L` to disable the service also clears all lock state.

## Target Selection Rule

If the detector returns multiple candidates during the detection phase, the selected target is the one whose box center is nearest to the ROI center point.

Distance is computed entirely in ROI-local coordinates so the logic stays independent of monitor placement.

## Tracking Strategy

The current environment ships with `opencv-python`, not `opencv-contrib-python`, so built-in trackers such as `CSRT` are not available. The implementation should therefore use a lightweight template-matching tracker built on standard OpenCV primitives that are already available.

Recommended approach:

- initialize the tracker from the selected bounding box
- store a grayscale template crop for that box
- search in a padded region around the previous box using `cv2.matchTemplate`
- on success, update the locked box position
- on failure, increment the lost-frame counter

This preserves a zero-training workflow and avoids adding heavier dependencies.

## Lost-Frame Policy

- `lost_frames == 0`: normal tracking
- `1 <= lost_frames <= 5`: keep the previous locked box visible and continue tracking recovery attempts
- `lost_frames > 5`: clear the tracker and return to detection mode on the current active frame

This matches the requested “保留锁定，超过再重新搜索” behavior.

## Performance Strategy

The main performance rule remains: do as little full-frame detection as possible.

Priority order:

1. no work while inactive
2. one full-frame detection only when no lock exists
3. single-target tracking while locked
4. only re-detect after the lost-frame threshold is exceeded
5. still render only one box in the overlay

Compared with repeated multi-person detection, this reduces steady-state inference cost during long left-mouse holds.

## Validation Plan

- Unit test target selection by ROI-center distance.
- Unit test tracking success and failure behavior in a pure tracker test.
- Unit test runtime lock lifecycle:
  - detect and lock one target
  - ignore other detections while locked
  - preserve lock for up to 5 lost frames
  - re-detect after the 6th lost frame
  - clear lock on inactive transition
- Manual verification that only one box is shown during a left-mouse hold.
- Manual verification that a briefly lost target does not immediately trigger global re-detection.
