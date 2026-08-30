from __future__ import annotations

from enum import StrEnum


class PetState(StrEnum):
    IDLE = "idle"
    WALKING = "walking"
    THINKING = "thinking"
    LOADING = "loading"
    SUCCESS = "success"
    SLEEPING = "sleeping"


STATE_LABELS = {
    PetState.IDLE: "آماده‌ام",
    PetState.WALKING: "دارم می‌گردم",
    PetState.THINKING: "دارم فکر می‌کنم",
    PetState.LOADING: "در حال انجام ◌",
    PetState.SUCCESS: "انجام شد ✓",
    PetState.SLEEPING: "حالت کم‌مصرف",
}
