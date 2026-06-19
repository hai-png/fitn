"""
Nutrition plan orchestrator — combines RMR, TDEE, calories, macros, hydration, micros.
"""
from __future__ import annotations

from ..models.profile import UserProfile, Sex
from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.nutrition import NutritionPlan
from .rmr import compute_rmr
from .tdee import compute_tdee
from .calories import compute_calorie_targets, BULK_RATE_BY_STATUS
from .macros import compute_macros
from .hydration import compute_hydration
from .micronutrients import compute_micronutrients


def build_nutrition_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    exercise_hours_per_day: float = 1.0,
    exercise_intensity: str = "moderate",
    climate: str = "temperate",
    in_active_deficit: bool = False,
    weight_reduced_pct: float = 0.0,
) -> NutritionPlan:
    """
    Build the complete nutrition plan from profile + assessment.

    Pipeline:
      RMR → TDEE → Calorie targets → Macros → Hydration + Micros → Timeline
    """
    # 1. RMR
    rmr = compute_rmr(
        profile=profile,
        body_fat_pct=assessment.body_composition.body_fat_pct,
        in_active_deficit=in_active_deficit,
        weight_reduced_pct=weight_reduced_pct,
    )

    # 2. TDEE
    tdee = compute_tdee(rmr, profile)

    # 3. Calorie targets
    # Determine if user is in active deficit for adaptation
    active_deficit = (
        assessment.recommended_strategy == RecommendedStrategy.CUT
        or assessment.recommended_strategy == RecommendedStrategy.RECOMP
    )
    calories = compute_calorie_targets(
        profile=profile,
        tdee_kcal=tdee.final_tdee_kcal,
        strategy=assessment.recommended_strategy,
        body_fat_pct=assessment.body_composition.body_fat_pct,
        in_active_deficit=active_deficit,
    )

    # 4. Macros
    macros = compute_macros(
        profile=profile,
        body_fat_pct=assessment.body_composition.body_fat_pct,
        strategy=assessment.recommended_strategy,
        calorie_targets=calories,
    )

    # 5. Hydration
    hydration = compute_hydration(
        profile=profile,
        exercise_hours_per_day=exercise_hours_per_day,
        exercise_intensity=exercise_intensity,
        climate=climate,
    )

    # 6. Micronutrients
    micros = compute_micronutrients(calories.target_calories_kcal)

    # 7. Estimate timeline
    timeline_weeks = _estimate_timeline(
        profile=profile,
        assessment=assessment,
        calorie_targets=calories,
    )

    notes = [
        f"RMR formula: {rmr.formula.value}",
        f"Activity factor: {tdee.activity_factor}",
        f"Strategy: {assessment.recommended_strategy.value}",
        f"Estimated timeline to goal: {timeline_weeks} weeks",
    ]

    return NutritionPlan(
        rmr=rmr,
        tdee=tdee,
        calories=calories,
        macros=macros,
        hydration=hydration,
        micronutrients=micros,
        timeline_weeks=timeline_weeks,
        notes=notes,
    )


def _estimate_timeline(
    profile: UserProfile,
    assessment: AssessmentResult,
    calorie_targets,
) -> int:
    """
    Estimate timeline (weeks) to reach the target state.

    - Cut: time to reach operational_lo BF% (10% M / 18% F) at target rate
    - Bulk: time to reach FFMI ceiling or operational_hi BF%
    - Maintenance / Recomp: 12 weeks (typical mesocycle)
    """
    from ..assessment.decision import CUT_BULK_BOUNDARIES

    strategy = assessment.recommended_strategy
    b = CUT_BULK_BOUNDARIES[profile.sex]
    bf_pct = assessment.body_composition.body_fat_pct
    weight_kg = profile.weight_kg

    if strategy == RecommendedStrategy.CUT:
        target_bf = b["operational_lo"] + 2  # aim for just above cut floor
        target_weight = assessment.body_composition.lean_body_mass_kg / (1 - target_bf / 100)
        kg_to_lose = max(0, weight_kg - target_weight)
        weekly_rate_kg = weight_kg * calorie_targets.rate_pct
        if weekly_rate_kg <= 0:
            return 12
        return max(4, int(kg_to_lose / weekly_rate_kg) + 4)   # +4 for adaptation

    if strategy == RecommendedStrategy.BULK:
        # Estimate time to add 5% BW (reasonable bulk duration)
        target_gain_kg = weight_kg * 0.05
        monthly_rate_kg = weight_kg * calorie_targets.rate_pct
        if monthly_rate_kg <= 0:
            return 16
        return max(12, int(target_gain_kg / monthly_rate_kg * 4.345) + 4)

    if strategy == RecommendedStrategy.RECOMP:
        return 12   # standard recomp assessment window

    if strategy == RecommendedStrategy.MAINTENANCE:
        return 12

    if strategy == RecommendedStrategy.HABIT_CHANGE_FIRST:
        return 8    # 8 weeks of habit change before calorie counting

    return 12


__all__ = ["build_nutrition_plan"]
