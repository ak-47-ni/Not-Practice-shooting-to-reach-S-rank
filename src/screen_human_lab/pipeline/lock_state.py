from __future__ import annotations

from enum import Enum


class LockStatus(str, Enum):
    IDLE = "idle"
    ACQUIRING = "acquiring"
    LOCKED = "locked"
    RECOVERING = "recovering"


class LockStateMachine:
    def __init__(self, *, max_lost_frames: int = 5) -> None:
        self._max_lost_frames = max(max_lost_frames, 0)
        self._status = LockStatus.IDLE
        self._lost_frames = 0

    @property
    def status(self) -> LockStatus:
        return self._status

    @property
    def lost_frames(self) -> int:
        return self._lost_frames

    def begin_acquiring(self) -> None:
        if self._status is LockStatus.IDLE:
            self._status = LockStatus.ACQUIRING

    def lock_acquired(self) -> None:
        self._status = LockStatus.LOCKED
        self._lost_frames = 0

    def mark_lost(self) -> bool:
        self._lost_frames += 1
        if self._lost_frames > self._max_lost_frames:
            self.clear()
            return False
        self._status = LockStatus.RECOVERING
        return True

    def clear(self) -> None:
        self._status = LockStatus.IDLE
        self._lost_frames = 0
