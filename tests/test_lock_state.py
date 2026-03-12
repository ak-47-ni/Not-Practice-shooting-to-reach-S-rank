from screen_human_lab.pipeline.lock_state import LockStateMachine, LockStatus


def test_lock_state_machine_tracks_acquire_recover_and_reset() -> None:
    machine = LockStateMachine(max_lost_frames=2)

    assert machine.status is LockStatus.IDLE

    machine.begin_acquiring()
    assert machine.status is LockStatus.ACQUIRING

    machine.lock_acquired()
    assert machine.status is LockStatus.LOCKED
    assert machine.lost_frames == 0

    machine.mark_lost()
    assert machine.status is LockStatus.RECOVERING
    assert machine.lost_frames == 1

    machine.lock_acquired()
    assert machine.status is LockStatus.LOCKED
    assert machine.lost_frames == 0

    machine.mark_lost()
    machine.mark_lost()
    machine.mark_lost()
    assert machine.status is LockStatus.IDLE
    assert machine.lost_frames == 0
