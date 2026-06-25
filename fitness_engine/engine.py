"""
Fitness Engine — top-level orchestrator.

Clean information flow:

    UserProfile
        ↓
    assess_profile(profile) → AssessmentResult
        ↓
    propose_plan(profile, assessment, preferences?) → FitnessPlan
        ├── build_nutrition_plan(profile, assessment, prefs.nutrition)
        ├── build_training_plan(profile, assessment, prefs.training)
        └── build_meal_plan(profile, assessment, nutrition, prefs.meal)

Public API:
    from fitness_engine import (
        UserProfile, assess_profile, propose_plan, PlanPreferences,
    )

    profile = UserProfile(...)
    assessment = assess_profile(profile)
    preferences = PlanPreferences(meal_frequency=4, include_pre_post_workout=True)
    plan = propose_plan(profile, assessment, preferences)

Backward compatibility: the flat-kwargs signature still works:

    plan = propose_plan(
        profile, assessment,
        meal_frequency=4,
        include_pre_post_workout=True,
    )
"""
from __future__ import annotations

import warnings

from .models.profile import UserProfile
from .models.assessment import AssessmentResult, RecommendedStrategy
from .models.training import PlanType
from .models.meal import FitnessPlan
from .models.preferences import PlanPreferences
from .assessment.assessor import assess_profile
from .nutrition.planner import build_nutrition_plan
from .training.architect import build_training_plan
from .meal_plan.planner import build_meal_plan


def propose_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    preferences: PlanPreferences | None = None,
    # === Backward-compat flat kwargs (deprecated, use PlanPreferences) ===
    meal_frequency: int | None = None,
    exercise_hours_per_day: float | None = None,
    exercise_intensity: str | None = None,
    climate: str | None = None,
    in_active_deficit: bool | None = None,
    weight_reduced_pct: float | None = None,
    plan_type: PlanType | None = None,
    muscle_focus: list[str] | None = None,
    program_duration_weeks: int | None = None,
    cuisine_preference: str | None = None,
    allergens_to_avoid: list[str] | None = None,
    excluded_ingredients: list[str] | None = None,
    include_pre_post_workout: bool | None = None,
) -> FitnessPlan:
    """
    Build the complete fitness plan: nutrition + training + meal plan.

    Args:
      profile: user profile
      assessment: assessment result (from assess_profile)
      preferences: optional PlanPreferences dataclass grouping all tunable
                   preferences. If None, default preferences are used.

    Backward-compat kwargs (deprecated — prefer PlanPreferences):
      meal_frequency, exercise_hours_per_day, exercise_intensity, climate,
      in_active_deficit, weight_reduced_pct, plan_type, muscle_focus,
      program_duration_weeks, cuisine_preference, allergens_to_avoid,
      excluded_ingredients, include_pre_post_workout

    Returns FitnessPlan.
    """
    # === Resolve preferences ===
    if preferences is None:
        preferences = PlanPreferences()

    # Collect any flat kwargs and merge via from_kwargs (single coercion path).
    # Phase-6 cleanup: consolidated 13 inline conditionals + 2 deferred imports
    # into one dict + one from_kwargs call. Emits DeprecationWarning.
    flat_kwargs: dict = {}
    if meal_frequency is not None:
        flat_kwargs["meal_frequency"] = meal_frequency
    if exercise_hours_per_day is not None:
        flat_kwargs["exercise_hours_per_day"] = exercise_hours_per_day
    if exercise_intensity is not None:
        flat_kwargs["exercise_intensity"] = exercise_intensity
    if climate is not None:
        flat_kwargs["climate"] = climate
    if in_active_deficit is not None:
        flat_kwargs["in_active_deficit"] = in_active_deficit
    if weight_reduced_pct is not None:
        flat_kwargs["weight_reduced_pct"] = weight_reduced_pct
    if plan_type is not None:
        flat_kwargs["plan_type"] = plan_type
    if muscle_focus is not None:
        flat_kwargs["muscle_focus"] = muscle_focus
    if program_duration_weeks is not None:
        flat_kwargs["program_duration_weeks"] = program_duration_weeks
    if cuisine_preference is not None:
        flat_kwargs["cuisine_preference"] = cuisine_preference
    if allergens_to_avoid is not None:
        flat_kwargs["allergens_to_avoid"] = allergens_to_avoid
    if excluded_ingredients is not None:
        flat_kwargs["excluded_ingredients"] = excluded_ingredients
    if include_pre_post_workout is not None:
        flat_kwargs["include_pre_post_workout"] = include_pre_post_workout

    if flat_kwargs:
        warnings.warn(
            "propose_plan() flat kwargs are deprecated. Pass a PlanPreferences "
            "dataclass as the third argument instead. Flat kwargs will be "
            "removed in a future major version.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Build a fresh PlanPreferences from the flat kwargs (handles enum
        # coercion via __post_init__), then overlay onto existing preferences.
        from_kwargs_prefs = PlanPreferences.from_kwargs(**flat_kwargs)
        for field_name in flat_kwargs:
            setattr(preferences, field_name, getattr(from_kwargs_prefs, field_name))

    # === 1. Nutrition plan ===
    nutrition = build_nutrition_plan(
        profile=profile,
        assessment=assessment,
        exercise_hours_per_day=preferences.exercise_hours_per_day,
        exercise_intensity=preferences.exercise_intensity,
        climate=preferences.climate,
        in_active_deficit=preferences.in_active_deficit,
        weight_reduced_pct=preferences.weight_reduced_pct,
    )

    # === 2. Training plan ===
    training = build_training_plan(
        profile=profile,
        assessment=assessment,
        plan_type=preferences.plan_type,
        muscle_focus=preferences.muscle_focus,
        program_duration_weeks=preferences.program_duration_weeks,
    )

    # === 3. Meal plan ===
    meal = build_meal_plan(
        profile=profile,
        assessment=assessment,
        nutrition=nutrition,
        meal_frequency=preferences.meal_frequency,
        cuisine_preference=preferences.cuisine_preference,
        allergens_to_avoid=preferences.allergens_to_avoid,
        excluded_ingredients=preferences.excluded_ingredients,
        include_pre_post_workout=preferences.include_pre_post_workout,
    )

    # === 4. Build unified summary ===
    summary = _build_summary(profile, assessment, nutrition, training, meal, preferences)

    return FitnessPlan(
        nutrition=nutrition,
        training=training,
        meal=meal,
        summary=summary,
    )


def _build_summary(
    profile: UserProfile,
    assessment: AssessmentResult,
    nutrition,
    training,
    meal,
    preferences: PlanPreferences,
) -> str:
    """Build a human-readable plan summary."""
    plan_type_label = training.plan_type.value.upper()
    duration_label = (
        f" ({training.total_duration_weeks} weeks)"
        if training.total_duration_weeks > 0
        else " (ongoing rotation)"
    )

    parts = [
        "=== Fitness Plan Summary ===",
        f"User: {profile.sex.value}, {profile.age}y, "
        f"{profile.height_cm:.0f}cm, {profile.weight_kg:.1f}kg",
        f"Assessment: BF={assessment.body_composition.body_fat_pct:.1f}% "
        f"({assessment.body_composition.body_fat_category.value}), "
        f"BMI={assessment.body_composition.bmi:.1f}, "
        f"FFMI={assessment.body_composition.ffmi:.1f}",
        f"Strategy: {assessment.recommended_strategy.value.upper()}",
        f"  — {assessment.strategy_rationale}",
        "",
        "Nutrition:",
        f"  • TDEE: {nutrition.tdee.final_tdee_kcal:.0f} kcal",
        f"  • Target: {nutrition.calories.target_calories_kcal:.0f} kcal "
        f"({nutrition.calories.calorie_delta_kcal:+.0f} vs TDEE)",
        f"  • Macros: P{nutrition.macros.protein_g:.0f}g / "
        f"C{nutrition.macros.carb_g:.0f}g / F{nutrition.macros.fat_g:.0f}g",
        f"  • Hydration: {nutrition.hydration.water_liters_per_day:.1f} L/day",
        f"  • Fiber: {nutrition.micronutrients.fiber_g:.0f} g/day",
        f"  • Timeline: ~{nutrition.timeline_weeks} weeks to goal",
        "",
        "Training:",
        f"  • Plan type: {plan_type_label}{duration_label}",
        f"  • Goal: {training.goal.value}",
        f"  • Split: {training.split_type.value} "
        f"({training.training_days_per_week}d/wk)",
        f"  • Progression: {training.progression.value}",
    ]
    if training.mesocycles:
        parts.append(
            f"  • Mesocycles: {len(training.mesocycles)} × "
            f"{training.mesocycles[0].duration_weeks}w (with deload)"
        )
        parts.append(
            f"  • Workouts per cycle: "
            f"{len(training.mesocycles[0].microcycles[0].workouts)}"
        )
    if training.muscle_focus:
        parts.append(f"  • Muscle focus: {', '.join(training.muscle_focus)}")
    parts.extend([
        "",
        "Meal plan:",
        f"  • Frequency: {meal.meal_frequency} meals/day"
        + (f" (+ PRE/POST workout on training days)"
           if preferences.include_pre_post_workout else ""),
        "  • Template: 7-day rotation",
        f"  • Daily target: {nutrition.calories.target_calories_kcal:.0f} kcal",
    ])
    if preferences.cuisine_preference:
        parts.append(f"  • Cuisine preference: {preferences.cuisine_preference}")
    if preferences.allergens_to_avoid:
        parts.append(f"  • Allergens avoided: {', '.join(preferences.allergens_to_avoid)}")

    return "\n".join(parts)


__all__ = [
    "UserProfile",
    "AssessmentResult",
    "RecommendedStrategy",
    "FitnessPlan",
    "PlanPreferences",
    "assess_profile",
    "propose_plan",
]
