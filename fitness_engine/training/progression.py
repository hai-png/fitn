"""
Progressive overload schemes.

Phase-1 implements basic linear and DUP schemes. Future versions will add
block periodization and advanced progression algorithms.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProgressionState(str, Enum):
    INCREASING = "increasing"      # adding load
    STALLED = "stalled"            # failed to add load for 2+ sessions
    DELOAD_NEEDED = "deload_needed"


@dataclass
class ProgressionEntry:
    """One session's progression data."""
    session_number: int
    exercise_name: str
    weight_kg: float
    sets_completed: int
    reps_per_set: list[int]
    rpe: float
    state: ProgressionState = ProgressionState.INCREASING


def linear_progression_next(
    current_weight_kg: float,
    last_reps_achieved: list[int],
    target_reps: tuple[int, int],   # (low, high), e.g. (5, 8)
    increment_kg: float = 2.5,
) -> tuple[float, str]:
    """
    Linear progression: add weight when target reps are achieved in all sets.

    Returns (next_weight, explanation).
    """
    low, high = target_reps
    all_at_target = all(reps >= high for reps in last_reps_achieved)

    if all_at_target and len(last_reps_achieved) >= 3:
        next_weight = current_weight_kg + increment_kg
        return next_weight, (
            f"All sets achieved {high}+ reps → +{increment_kg}kg "
            f"({current_weight_kg} → {next_weight}kg)"
        )
    elif all(reps >= low for reps in last_reps_achieved):
        # Stay at current weight, aim for more reps
        return current_weight_kg, (
            f"Reps in target range but not all ≥ {high} → repeat {current_weight_kg}kg"
        )
    else:
        # Failed to hit minimum reps — deload 10%
        deload_weight = current_weight_kg * 0.90
        return deload_weight, (
            f"Failed to hit {low} reps in all sets → deload 10% "
            f"({current_weight_kg} → {deload_weight:.1f}kg)"
        )


def dup_next(
    current_weights: dict[str, float],   # day_type → weight, e.g. {"heavy": 100, "moderate": 90, "light": 80}
    last_reps: dict[str, list[int]],     # day_type → reps achieved
) -> dict[str, tuple[float, str]]:
    """
    Daily Undulating Periodization: rotate heavy/moderate/light days.

    Each day type progresses independently with linear progression rules.
    """
    next_state = {}
    targets = {"heavy": (3, 5), "moderate": (8, 10), "light": (12, 15)}
    for day_type, weight in current_weights.items():
        reps = last_reps.get(day_type, [])
        if reps:
            next_w, expl = linear_progression_next(
                weight, reps, targets[day_type], increment_kg=2.5
            )
            next_state[day_type] = (next_w, expl)
        else:
            next_state[day_type] = (weight, "no data yet")
    return next_state


__all__ = [
    "ProgressionState", "ProgressionEntry",
    "linear_progression_next", "dup_next",
]
