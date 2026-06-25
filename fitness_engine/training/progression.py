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

    if all_at_target and len(last_reps_achieved) >= 1:
        # Tier 2.28 fix: was `>= 3`, which meant 2-set exercises (common for
        # accessories, deloads, isolation) could never trigger progression.
        # Now `>= 1` — any exercise with at least 1 set can progress when all
        # sets hit the top of the rep target.
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


def double_progression_next(
    current_weight_kg: float,
    reps_achieved: list[int],
    reps_target_lo: int,
    reps_target_hi: int,
    increment_kg: float = 2.5,
) -> tuple[float, int, str]:
    """
    Double progression (RIR-based): add reps until top of range at all sets,
    then add weight and drop reps back to the bottom of the range.

    Rules:
      - If ALL sets achieved reps_target_hi: add weight, reset target to reps_target_lo.
      - If ALL sets achieved reps_target_lo (but not all hit hi): keep weight, target hi.
      - Otherwise: keep weight, target lo (repeat).

    Tier 2.29 fix: this function was referenced in the architect docstring
    but never implemented. The RIR-based progression model that the intensity_model
    RIR table supports is now available.

    Args:
      current_weight_kg: current working weight
      reps_achieved: list of reps achieved in each set last session
      reps_target_lo: bottom of the rep target range (e.g. 8 for 8-12)
      reps_target_hi: top of the rep target range (e.g. 12 for 8-12)
      increment_kg: weight to add when progressing (default 2.5kg)

    Returns:
      (next_weight_kg, next_reps_target, explanation)
    """
    if not reps_achieved:
        return current_weight_kg, reps_target_lo, "No rep data — repeat at current weight."

    all_hit_hi = all(reps >= reps_target_hi for reps in reps_achieved)
    all_hit_lo = all(reps >= reps_target_lo for reps in reps_achieved)

    if all_hit_hi:
        # All sets hit the top of the range → add weight, reset to bottom
        next_weight = current_weight_kg + increment_kg
        return next_weight, reps_target_lo, (
            f"Double progression: all sets achieved {reps_target_hi}+ reps → "
            f"+{increment_kg}kg ({current_weight_kg} → {next_weight}kg), "
            f"reset target to {reps_target_lo}-{reps_target_hi}."
        )
    elif all_hit_lo:
        # All sets in range but not all at top → keep weight, push for more reps
        return current_weight_kg, reps_target_hi, (
            f"Double progression: all sets achieved {reps_target_lo}+ reps but not all "
            f"hit {reps_target_hi} → repeat {current_weight_kg}kg, target {reps_target_hi} reps."
        )
    else:
        # Failed to hit minimum → keep weight, target lo
        return current_weight_kg, reps_target_lo, (
            f"Double progression: not all sets hit {reps_target_lo} reps → "
            f"repeat {current_weight_kg}kg, target {reps_target_lo}-{reps_target_hi}."
        )


__all__ = [
    "ProgressionState", "ProgressionEntry",
    "linear_progression_next", "dup_next", "double_progression_next",
]
