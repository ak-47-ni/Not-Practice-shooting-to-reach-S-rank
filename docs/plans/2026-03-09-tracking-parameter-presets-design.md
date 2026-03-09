# Tracking Parameter Presets Design

**Date:** 2026-03-09

**Goal:** Make the single-target template tracker configurable from YAML and add stable/fast preset files for both MPS and CPU runtimes without breaking the existing config files.

## Scope

- Add a dedicated `tracking` config section.
- Expose `match_threshold` and `search_padding` as YAML fields.
- Keep the existing `configs/realtime_mps.yaml` and `configs/realtime_cpu.yaml` working.
- Add four new preset files:
  - `configs/realtime_mps_stable.yaml`
  - `configs/realtime_mps_fast.yaml`
  - `configs/realtime_cpu_stable.yaml`
  - `configs/realtime_cpu_fast.yaml`
- Route the parsed tracking parameters into `TemplateMatchTracker`.
- Document the preset intent and usage.

## Out of Scope

- Adding CLI flags for tracker tuning.
- Changing the lost-frame policy.
- Supporting multiple tracker implementations.
- Removing or renaming the current baseline config files.

## Configuration Shape

Add a new top-level section:

```yaml
tracking:
  match_threshold: 0.55
  search_padding: 36
```

This keeps tracking concerns separate from `overlay` and `inference`, and makes future additions like `max_lost_frames` or `tracker_type` straightforward.

## Defaults and Compatibility

Backward compatibility matters because the current baseline YAML files do not have a `tracking` section.

Recommended defaults:

- `match_threshold: 0.45`
- `search_padding: 24`

These match the current tracker constructor defaults so older config files continue to behave the same way after the parser change.

## Preset Matrix

Keep the current files unchanged and add four new presets:

- **Stable presets**
  - `match_threshold: 0.55`
  - `search_padding: 36`
- **Fast presets**
  - `match_threshold: 0.45`
  - `search_padding: 24`

Per backend:

- `realtime_mps_stable.yaml`
- `realtime_mps_fast.yaml`
- `realtime_cpu_stable.yaml`
- `realtime_cpu_fast.yaml`

This makes the trade-off explicit and avoids mutating the user's current default launch commands.

## Runtime Wiring

The runtime already owns tracker creation, so the cleanest path is:

1. parse `TrackingConfig` in `config.py`
2. carry it through `AppConfig`
3. build `TemplateMatchTracker(match_threshold=..., search_padding=...)` in `cli.py` or via an injected tracker factory
4. keep `GatedDetectionRuntime` responsible for using the tracker, not for parsing config

This preserves separation of concerns: config parsing stays in config, tracker behavior stays in tracking, and runtime orchestration stays in the pipeline layer.

## Validation Plan

- Unit test `TrackingConfig` parsing and defaults.
- Unit test that missing `tracking` config falls back to compatibility defaults.
- Unit test or integration test that the runtime uses the configured tracker values.
- Test that all four preset files exist and contain the expected tracking keys.
- Document the stable vs fast trade-off in `README.md`.
