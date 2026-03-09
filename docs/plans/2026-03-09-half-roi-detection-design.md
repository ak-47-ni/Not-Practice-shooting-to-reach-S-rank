# Half ROI Detection Design

**Date:** 2026-03-09

**Goal:** Reduce the real centered ROI capture and detection region from `1000x1000` to `500x500`, while keeping detection boxes at their true model output size.

## Scope

- Shrink the true centered ROI used by capture, inference, overlay boundary, `dx/dy`, and cursor-follow reference.
- Keep the red detection box at the detector's real output size.
- Keep the straight-line cursor-follow behavior.
- Keep the fallback to ROI center when the current cursor position cannot be read.

## Out of Scope

- Separate display ROI and inference ROI.
- Additional internal re-cropping layers after capture.
- Changing the target-selection strategy.

## Corrected Requirement

The previous implementation mistakenly shrank the detection bounding box itself. That was the wrong interpretation.

The actual requirement is:

- shrink the **real ROI detection area** by half on both width and height
- keep the ROI centered on the selected monitor
- keep detection boxes at their true output size inside that smaller ROI

For the current presets, this means changing `roi_size` from `1000` to `500`.

## Recommended Approach

Use the existing centered-ROI architecture and change the source of truth at the capture layer.

1. Keep `compute_center_square_roi(...)` unchanged.
2. Update the runtime preset files so the requested centered square ROI becomes `500`.
3. Remove the mistaken bbox-halving logic from `GatedDetectionRuntime`.
4. Let overlay rendering, `dx/dy`, and cursor-follow continue consuming the true detection boxes from the smaller ROI.

This keeps the pipeline simple and correct because every downstream module already trusts capture ROI geometry.

## Data Flow

- `CaptureConfig.roi_size` determines the real centered ROI.
- `MSSCapture` grabs only that smaller square region.
- `GatedDetectionRuntime` keeps and emits the detector/tracker bbox without extra shrinking.
- `OverlayView` draws the smaller ROI boundary and the true detection boxes.
- `dx/dy` and cursor-follow continue using the true detection center.

## Validation Plan

- Unit test the runtime so selected and tracked boxes keep their original size.
- Update preset tests so the default runtime configs expect `roi_size: 500`.
- Keep cursor fallback and speed/min-distance tests unchanged.
- Run full regression coverage.

