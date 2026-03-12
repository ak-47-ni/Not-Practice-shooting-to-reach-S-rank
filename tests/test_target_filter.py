from screen_human_lab.pipeline.target_filter import TargetStateFilter


def test_target_state_filter_smooths_jittery_bbox_updates() -> None:
    state_filter = TargetStateFilter(smoothing_factor=0.5)

    first = state_filter.update((10, 20, 30, 40))
    second = state_filter.update((14, 24, 34, 44))

    assert first == (10, 20, 30, 40)
    assert second == (12, 22, 32, 42)


def test_target_state_filter_reset_clears_previous_state() -> None:
    state_filter = TargetStateFilter(smoothing_factor=0.25)
    state_filter.update((10, 20, 30, 40))

    state_filter.reset()
    result = state_filter.update((30, 40, 50, 60))

    assert result == (30, 40, 50, 60)
