"""
Fitness Engine — top-level orchestrator.

Public API:
    from fitness_engine import UserProfile, assess_profile, propose_plan

    profile = UserProfile(...)
    assessment = assess_profile(profile)
    plan = propose_plan(profile, assessment)

Phase-3 additions:
    plan = propose_plan(
        profile, assessment,
        plan_type=PlanType.PROGRAM,         # STANDARD | PROGRAM
        muscle_focus=["chest", "arms"],     # optional emphasis
        program_duration_weeks=12,          # optional override
    )
"""
from __future__ import annotations

from .models.profile import UserProfile
from .models.assessment import AssessmentResult, RecommendedStrategy
from .models.training import PlanType
from .models.meal import FitnessPlan
from .assessment.assessor import assess_profile
from .nutrition.planner import build_nutrition_plan
from .training.architect import build_training_plan
from .meal_plan.planner import build_meal_plan


def propose_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    meal_frequency: int = 3,
    exercise_hours_per_day: float = 1.0,
    exercise_intensity: str = "moderate",
    climate: str = "temperate",
    in_active_deficit: bool = False,
    weight_reduced_pct: float = 0.0,
    # Phase-3 training parameters
    plan_type: PlanType | None = None,
    muscle_focus: list[str] | None = None,
    program_duration_weeks: int | None = None,
    # Phase-2 meal parameter
    cuisine_preference: str | None = None,
) -> FitnessPlan:
    """
    Build the complete fitness plan: nutrition + training + meal plan.

    Args:
      profile: user profile
      assessment: assessment result (from assess_profile)
      meal_frequency: 2-5 meals per day (default 3)
      exercise_hours_per_day: for hydration calc (default 1)
      exercise_intensity: light/moderate/intense (default moderate)
      climate: cold/temperate/hot/hot_humid (default temperate)
      in_active_deficit: True if user is currently cutting (default False)
      weight_reduced_pct: 0-1, fraction below all-time high (default 0)

      plan_type: PlanType.STANDARD (ongoing rotation) or PlanType.PROGRAM
                 (time-bound with mesocycles). None = auto-decide.
      muscle_focus: optional list of muscle groups to emphasize
                    (e.g. ["chest", "arms"]).
      program_duration_weeks: override the auto-computed program duration.
      cuisine_preference: optional recipe cuisine filter (e.g. "ethiopian").

    Returns FitnessPlan.
    """
    # 1. Nutrition plan
    nutrition = build_nutrition_plan(
        profile=profile,
        assessment=assessment,
        exercise_hours_per_day=exercise_hours_per_day,
        exercise_intensity=exercise_intensity,
        climate=climate,
        in_active_deficit=in_active_deficit,
        weight_reduced_pct=weight_reduced_pct,
    )

    # 2. Training plan (Phase-3 architect)
    training = build_training_plan(
        profile=profile,
        assessment=assessment,
        plan_type=plan_type,
        muscle_focus=muscle_focus,
        program_duration_weeks=program_duration_weeks,
    )

    # 3. Meal plan
    meal = build_meal_plan(
        profile=profile,
        assessment=assessment,
        nutrition=nutrition,
        meal_frequency=meal_frequency,
        cuisine_preference=cuisine_preference,
    )

    # 4. Build summary
    plan_type_label = training.plan_type.value.upper()
    duration_label = (
        f" ({training.total_duration_weeks} weeks)"
        if training.total_duration_weeks > 0
        else " (ongoing rotation)"
    )
    summary_parts = [
        "=== Fitness Plan Summary ===",
        f"User: {profile.sex.value}, {profile.age}y, "
        f"{profile.height_cm:.0f}cm, {profile.weight_kg:.1f}kg",
        f"Assessment: BF={assessment.body_composition.body_fat_pct:.1f}% "
        f"({assessment.body_composition.body_fat_category.value}), "
        f"BMI={assessment.body_composition.bmi:.1f}, "
        f"FFMI={assessment.body_composition.ffmi:.1f}",
        f"Strategy: {assessment.recommended_strategy.value.upper()}",
        f"  — {assessment.strategy_rationale}",
        "Nutrition:",
        f"  • TDEE: {nutrition.tdee.final_tdee_kcal:.0f} kcal",
        f"  • Target: {nutrition.calories.target_calories_kcal:.0f} kcal "
        f"({nutrition.calories.calorie_delta_kcal:+.0f} vs TDEE)",
        f"  • Macros: P{nutrition.macros.protein_g:.0f}g / "
        f"C{nutrition.macros.carb_g:.0f}g / F{nutrition.macros.fat_g:.0f}g",
        f"  • Hydration: {nutrition.hydration.water_liters_per_day:.1f} L/day",
        f"  • Fiber: {nutrition.micronutrients.fiber_g:.0f} g/day",
        f"  • Timeline: ~{nutrition.timeline_weeks} weeks to goal",
        "Training:",
        f"  • Plan type: {plan_type_label}{duration_label}",
        f"  • Goal: {training.goal.value}",
        f"  • Split: {training.split_type.value} "
        f"({training.training_days_per_week}d/wk)",
        f"  • Progression: {training.progression.value}",
    ]
    if training.mesocycles:
        summary_parts.append(
            f"  • Mesocycles: {len(training.mesocycles)} × "
            f"{training.mesocycles[0].duration_weeks}w (with deload)"
        )
        summary_parts.append(
            f"  • Workouts per cycle: "
            f"{len(training.mesocycles[0].microcycles[0].workouts)}"
        )
    if training.muscle_focus:
        summary_parts.append(
            f"  • Muscle focus: {', '.join(training.muscle_focus)}"
        )
    summary_parts.extend([
        "Meal plan:",
        f"  • Frequency: {meal.meal_frequency} meals/day",
        "  • Template: 7-day rotation",
        f"  • Daily target: {nutrition.calories.target_calories_kcal:.0f} kcal",
    ])

    return FitnessPlan(
        nutrition=nutrition,
        training=training,
        meal=meal,
        summary="\n".join(summary_parts),
    )


__all__ = [
    "UserProfile",
    "AssessmentResult",
    "RecommendedStrategy",
    "FitnessPlan",
    "assess_profile",
    "propose_plan",
]
