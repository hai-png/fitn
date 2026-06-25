"""
Plan preferences — unified configuration for the fitness engine.

Groups all user-tunable preferences (that aren't part of the core
UserProfile) into a single dataclass. This replaces the 13-parameter
signature of `propose_plan()` with a cleaner 3-parameter signature:

    plan = propose_plan(profile, assessment, preferences)

The dataclass is also used by the sub-planners (nutrition, training, meal)
so the entire pipeline reads from a single source of truth.

Backward compatibility: `propose_plan()` still accepts the flat kwargs
for existing callers. Internally it constructs a PlanPreferences from
those kwargs.
"""
from __future__ import annotations

from dataclasses import dataclass

import logging

from .training import PlanType
from .profile import ExerciseIntensity, Climate


def _coerce_intensity(v: str | ExerciseIntensity | None) -> ExerciseIntensity:
    if v is None:
        return ExerciseIntensity.MODERATE
    if isinstance(v, ExerciseIntensity):
        return v
    if isinstance(v, str):
        try:
            return ExerciseIntensity(v.lower())
        except ValueError:
            return ExerciseIntensity.MODERATE
    return ExerciseIntensity.MODERATE


def _coerce_climate(v: str | Climate | None) -> Climate:
    if v is None:
        return Climate.TEMPERATE
    if isinstance(v, Climate):
        return v
    if isinstance(v, str):
        try:
            return Climate(v.lower())
        except ValueError:
            return Climate.TEMPERATE
    return Climate.TEMPERATE


@dataclass
class PlanPreferences:
    """
    User-tunable preferences for plan generation.

    All fields have sensible defaults; users only set what they care about.

    Phase-6 fix: `exercise_intensity` and `climate` are now properly typed
    as `ExerciseIntensity` and `Climate` enums (Tier 3.31 added the enums
    but PlanPreferences still used raw `str`). The dataclass accepts both
    string and enum values via `__post_init__` coercion for backward compat.

    Fields are grouped by which sub-planner consumes them:

    === Nutrition preferences ===
    exercise_hours_per_day:  for hydration calc (default 1.0)
    exercise_intensity:      ExerciseIntensity enum (LIGHT/MODERATE/INTENSE)
    climate:                 Climate enum (COLD/TEMPERATE/HOT/HOT_HUMID)
    weight_reduced_pct:      0-1, fraction below all-time high (default 0)

    === Training preferences ===
    plan_type:               PlanType.STANDARD (ongoing) or PROGRAM (time-bound).
                             None = auto-decide based on goal.
    muscle_focus:            optional list of muscle groups to emphasize
                             (e.g. ["chest", "arms"]).
    program_duration_weeks:  override the auto-computed program duration.

    === Meal plan preferences ===
    meal_frequency:          2-5 meals per day (default 3)
    cuisine_preference:      optional recipe cuisine filter (e.g. "ethiopian")
    allergens_to_avoid:      list of allergens to exclude from meal plan
                             (e.g. ["dairy", "gluten"])
    excluded_ingredients:    list of free-text ingredients to exclude
    include_pre_post_workout: add PRE/POST workout meals on training days
    """

    # === Nutrition ===
    exercise_hours_per_day: float = 1.0
    exercise_intensity: ExerciseIntensity | str = ExerciseIntensity.MODERATE
    climate: Climate | str = Climate.TEMPERATE
    weight_reduced_pct: float = 0.0

    # === Training ===
    plan_type: PlanType | None = None
    muscle_focus: list[str] | None = None
    program_duration_weeks: int | None = None

    # === Meal plan ===
    meal_frequency: int = 3
    cuisine_preference: str | None = None
    allergens_to_avoid: list[str] | None = None
    excluded_ingredients: list[str] | None = None
    include_pre_post_workout: bool = False

    def __post_init__(self) -> None:
        # coerce string values to enums for type safety.
        self.exercise_intensity = _coerce_intensity(self.exercise_intensity)
        self.climate = _coerce_climate(self.climate)
        # Validate weight_reduced_pct is in [0, 1]
        if not (0.0 <= self.weight_reduced_pct <= 1.0):
            raise ValueError(
                f"weight_reduced_pct must be in [0, 1], got {self.weight_reduced_pct}"
            )
        # Warn on unknown kwargs in from_kwargs
        # (handled in from_kwargs via logging)

    @classmethod
    def from_kwargs(cls, **kwargs) -> "PlanPreferences":
        """
        Build PlanPreferences from flat kwargs (backward compat).

        Phase-6: logs a warning for unknown kwargs (e.g. typos like
        `meal_freqency=4`) instead of silently dropping them.
        """
        # ``import logging`` is at module top.
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {}
        unknown = []
        for k, v in kwargs.items():
            if k in valid_fields:
                filtered[k] = v
            else:
                unknown.append(k)
        if unknown:
            logging.warning(
                "PlanPreferences.from_kwargs: ignoring unknown kwargs: %s",
                ", ".join(unknown),
            )
        return cls(**filtered)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        d = asdict(self)
        # Convert enums to their string values
        if self.plan_type is not None:
            d["plan_type"] = self.plan_type.value
        if isinstance(self.exercise_intensity, ExerciseIntensity):
            d["exercise_intensity"] = self.exercise_intensity.value
        if isinstance(self.climate, Climate):
            d["climate"] = self.climate.value
        return d


__all__ = ["PlanPreferences"]
