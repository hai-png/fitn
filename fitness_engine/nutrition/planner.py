"""
Nutrition plan orchestrator — combines RMR, TDEE, calories, macros, hydration, micros.
"""
from __future__ import annotations

from ..models.profile import UserProfile, Sex
from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.nutrition import NutritionPlan
from ..assessment.decision import CUT_BULK_BOUNDARIES
from .rmr import compute_rmr
from .tdee import compute_tdee
from .calories import compute_calorie_targets, BULK_RATE_BY_STATUS
from .macros import compute_macros
from .hydration import compute_hydration
from .micronutrients import compute_micronutrients
from ..utils.units import WEEKS_PER_MONTH


def build_nutrition_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    exercise_hours_per_day: float = 1.0,
    exercise_intensity: str = "moderate",
    climate: str = "temperate",
    weight_reduced_pct: float = 0.0,
) -> NutritionPlan:
    """
    Build the complete nutrition plan from profile + assessment.

    Pipeline:
      RMR → TDEE → Calorie targets → Macros → Hydration + Micros → Timeline

    Phase-6 note: adaptive TDEE (`update_tdee_with_logs` in tdee.py) is
    available but NOT wired into this pipeline — there is no intake/weight
    log persisted on the UserProfile yet (the `intake_log_kcal` /
    `weight_log_kg` fields are stubbed out as comments in profile.py).
    Once those fields are populated, the call site would be:
        if profile.weight_log_kg:
            tdee = update_tdee_with_logs(tdee, ...)
    between steps 2 and 3.
    """
    # derive `active_deficit` from strategy (single source of
    # truth). CUT and RECOMP both place the user in an energy deficit.
    active_deficit = assessment.recommended_strategy in (
        RecommendedStrategy.CUT,
        RecommendedStrategy.RECOMP,
    )

    # 1. RMR
    rmr = compute_rmr(
        profile=profile,
        body_fat_pct=assessment.body_composition.body_fat_pct,
        in_active_deficit=active_deficit,
        weight_reduced_pct=weight_reduced_pct,
    )

    # 2. TDEE
    tdee = compute_tdee(rmr, profile)

    # 3. Calorie targets
    calories = compute_calorie_targets(
        profile=profile,
        tdee_kcal=tdee.final_tdee_kcal,
        strategy=assessment.recommended_strategy,
        body_fat_pct=assessment.body_composition.body_fat_pct,
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
    strategy = assessment.recommended_strategy
    b = CUT_BULK_BOUNDARIES[profile.sex]
    ADAPTATION_BUFFER_WEEKS = 4     # extra weeks to account for metabolic adaptation
    DEFAULT_BULK_DURATION_GAIN_PCT = 0.05  # 5% BW target for bulk duration estimate
    DEFAULT_RECOMP_TIMELINE_WEEKS = 12
    DEFAULT_MAINTENANCE_TIMELINE_WEEKS = 12
    DEFAULT_CUT_TIMELINE_FALLBACK_WEEKS = 12
    DEFAULT_BULK_TIMELINE_FALLBACK_WEEKS = 16

    bf_pct = assessment.body_composition.body_fat_pct
    weight_kg = profile.weight_kg

    if strategy == RecommendedStrategy.CUT:
        target_bf = b["operational_lo"] + 2  # aim for just above cut floor
        target_weight = assessment.body_composition.lean_body_mass_kg / (1 - target_bf / 100)
        kg_to_lose = max(0, weight_kg - target_weight)
        weekly_rate_kg = weight_kg * calorie_targets.rate_pct
        if weekly_rate_kg <= 0:
            return DEFAULT_CUT_TIMELINE_FALLBACK_WEEKS
        return max(ADAPTATION_BUFFER_WEEKS, int(kg_to_lose / weekly_rate_kg) + ADAPTATION_BUFFER_WEEKS)

    if strategy == RecommendedStrategy.BULK:
        target_gain_kg = weight_kg * DEFAULT_BULK_DURATION_GAIN_PCT
        monthly_rate_kg = weight_kg * calorie_targets.rate_pct
        if monthly_rate_kg <= 0:
            return DEFAULT_BULK_TIMELINE_FALLBACK_WEEKS
        return max(12, int(target_gain_kg / monthly_rate_kg * WEEKS_PER_MONTH) + ADAPTATION_BUFFER_WEEKS)

    if strategy == RecommendedStrategy.RECOMP:
        return DEFAULT_RECOMP_TIMELINE_WEEKS

    if strategy == RecommendedStrategy.MAINTENANCE:
        return DEFAULT_MAINTENANCE_TIMELINE_WEEKS

    if strategy == RecommendedStrategy.HABIT_CHANGE_FIRST:
        # HABIT_CHANGE_FIRST returns maintenance calories from
        # compute_calorie_targets (no deficit), but the timeline estimate is
        # 8 weeks (the “habit-change phase” before formal calorie counting).
        # This asymmetry is intentional — the user spends 8 weeks building
        # adherence habits (sleep, steps, protein timing) before entering a
        # formal cut/bulk. The maintenance calories preserve LBM during that
        # habit-building phase.
        return 8    # 8 weeks of habit change before calorie counting

    return 12


__all__ = ["build_nutrition_plan"]
