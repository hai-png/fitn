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

from dataclasses import dataclass, field
from typing import Optional

from .training import PlanType


@dataclass
class PlanPreferences:
    """
    User-tunable preferences for plan generation.

    All fields have sensible defaults; users only set what they care about.

    Fields are grouped by which sub-planner consumes them:

    === Nutrition preferences ===
    exercise_hours_per_day:  for hydration calc (default 1.0)
    exercise_intensity:      "light" / "moderate" / "intense" (default "moderate")
    climate:                 "cold" / "temperate" / "hot" / "hot_humid"
    in_active_deficit:       True if user is currently cutting (default False)
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
    exercise_intensity: str = "moderate"
    climate: str = "temperate"
    in_active_deficit: bool = False
    weight_reduced_pct: float = 0.0

    # === Training ===
    plan_type: Optional[PlanType] = None
    muscle_focus: Optional[list[str]] = None
    program_duration_weeks: Optional[int] = None

    # === Meal plan ===
    meal_frequency: int = 3
    cuisine_preference: Optional[str] = None
    allergens_to_avoid: Optional[list[str]] = None
    excluded_ingredients: Optional[list[str]] = None
    include_pre_post_workout: bool = False

    @classmethod
    def from_kwargs(cls, **kwargs) -> "PlanPreferences":
        """
        Build PlanPreferences from flat kwargs (backward compat).

        Ignores unknown kwargs silently so callers passing extra params
        don't crash.
        """
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in kwargs.items() if k in valid_fields}
        return cls(**filtered)

    def to_dict(self) -> dict:
        from dataclasses import asdict
        d = asdict(self)
        # Convert PlanType enum to its string value
        if self.plan_type is not None:
            d["plan_type"] = self.plan_type.value
        return d


__all__ = ["PlanPreferences"]
