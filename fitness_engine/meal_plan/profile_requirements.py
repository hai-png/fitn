"""
Profile requirements calculator — Phase-5 clean meal planning.

Computes the full set of nutritional requirements for a given profile:
  - TDEE + target kcal (with cut/bulk/recomp/maintenance delta)
  - Macro split (protein / fat / carbs in grams)
  - Per-meal allocation (kcal + macros per slot)
  - Fiber + hydration targets
  - Pre/Post workout slot targets (when applicable)
  - Micronutrient priorities (per diet type)

This module is the SINGLE SOURCE OF TRUTH for "what should this user eat?".
The planner + allocator + scorer all consume its output.

Inputs: UserProfile + AssessmentResult + NutritionPlan (existing engine output)
Output: MealPlanRequirements dataclass (defined here)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus,
    PrimaryGoal, EquipmentAccess, DietType,
)
from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.nutrition import NutritionPlan, MacroSplit
from ..models.meal import MealType


# === Diet type mapping ===

DIET_TYPE_RECIPE_TAG = {
    DietType.OMNIVORE: "OMNI",
    DietType.VEGAN: "VEGAN",
    DietType.VEGETARIAN: "VEGAN",  # closest available
    # Phase-5 new types
}


def get_recipe_diet_tag(profile_diet: DietType) -> str:
    """
    Map the user's DietType to a recipe diet_types tag.

    The 4 user-requested diet types are:
      1. vegan              → VEGAN
      2. omni               → OMNI
      3. vegan+ethiopian    → VEGAN_ETHIOPIAN
      4. omni+ethiopian     → OMNI_ETHIOPIAN

    We need to detect the Ethiopian preference from cuisine_preference
    because the profile's DietType enum doesn't have ETHIOPIAN variants.
    """
    # Check for Ethiopian preference via profile.cuisine_preference (Phase-5 addition)
    # or via the diet_type itself if it's a Phase-5 enum value
    # Phase-6 cleanup: DietType is an Enum and always has ``.value``; the
    # hasattr shim was a leftover from before the field was typed as DietType.
    diet_str = profile_diet.value.upper()

    if "VEGAN_ETHIOPIAN" in diet_str or "VEGAN-ETHIOPIAN" in diet_str:
        return "VEGAN_ETHIOPIAN"
    if "OMNI_ETHIOPIAN" in diet_str or "OMNI-ETHIOPIAN" in diet_str:
        return "OMNI_ETHIOPIAN"
    if "VEGAN" in diet_str or "VEGETARIAN" in diet_str:
        return "VEGAN"
    return "OMNI"


# === Per-meal slot requirements ===

@dataclass
class MealSlotTarget:
    """Nutritional target for a single meal slot."""
    meal_type: MealType
    target_kcal: float
    target_protein_g: float
    target_carb_g: float
    target_fat_g: float
    target_fiber_g: float
    is_training_day_slot: bool = False
    timing_note: str = ""   # e.g. "60-90 min before workout"


# === Pre/Post workout target computation ===

def compute_pre_workout_target(
    daily_kcal: float,
    daily_protein_g: float,
    daily_carb_g: float,
    daily_fat_g: float,
) -> MealSlotTarget:
    """
    Pre-workout meal target — preserves daily macro totals (Phase-6 fix).

    High carb, moderate protein, low fat, low fiber (fast digestion).
    ~10% of daily kcal, eaten 60-90 min before training.

    The slot takes 10% of daily kcal AND 10% of each daily macro, then applies
    a within-slot re-allocation toward the pre-workout ratio (20% P / 65% C /
    15% F by kcal). The re-allocation is compensated by adjusting the standard
    slots (see `_make_residual_slot`) so the daily sum is exact.

    Previously, the fixed 20/65/15 split was applied to the slot kcal without
    any reference to the user's daily macros, breaking keto users (e.g. a
    keto user with daily C=50g would get C=32g in PRE alone — a 64% daily
    carb surplus from a single slot).
    """
    slot_kcal = daily_kcal * 0.10
    # Start with 10% of daily macros (preserves daily total when combined
    # with the residual-slot compensation in compute_meal_plan_requirements).
    base_p = daily_protein_g * 0.10
    base_c = daily_carb_g * 0.10
    base_f = daily_fat_g * 0.10
    # Apply within-slot re-allocation toward pre-workout ratio.
    target_p, target_c, target_f = _rebalance_slot_macros(
        slot_kcal, base_p, base_c, base_f, *PRE_WORKOUT_MACRO_RATIO,
    )
    return MealSlotTarget(
        meal_type=MealType.PRE_WORKOUT,
        target_kcal=slot_kcal,
        target_protein_g=target_p,
        target_carb_g=target_c,
        target_fat_g=target_f,
        target_fiber_g=2.0,   # low fiber for fast digestion
        is_training_day_slot=True,
        timing_note="60-90 min before workout",
    )


# Pre/Post workout macro override ratios (by kcal).
# These define the WITHIN-SLOT re-allocation; the slot's total kcal is fixed
# (PRE=10% daily, POST=15% daily). The remaining daily macros (90% / 85%)
# are distributed across standard meals via `_make_residual_slot`.
PRE_WORKOUT_MACRO_RATIO = (0.20, 0.65, 0.15)   # (P, C, F) by kcal
POST_WORKOUT_MACRO_RATIO = (0.35, 0.50, 0.15)  # (P, C, F) by kcal


def _rebalance_slot_macros(
    slot_kcal: float,
    base_p_g: float,
    base_c_g: float,
    base_f_g: float,
    target_ratio_p: float,
    target_ratio_c: float,
    target_ratio_f: float,
) -> tuple[float, float, float]:
    """
    Re-allocate macros within a slot's kcal budget toward a target ratio.

    The slot's total kcal is preserved exactly. The base macros (derived
    from a fraction of daily totals) are blended with the target ratio
    using a 50/50 weight: this preserves more of the user's daily macro
    signature (e.g. keto's high fat) while still shifting toward the
    workout-optimized ratio.

    For a keto user (P=100, C=50, F=167 @ 2000 kcal):
      PRE base (10%): P=10, C=5, F=16.7 → 197 kcal (close to 200)
      Target ratio (20/65/15): P=10, C=32.5, F=3.3 → 200 kcal
      Blended (50/50): P=10, C=18.75, F=10 → 200 kcal
    Net effect: keto user gets C=18.75g in PRE (vs 32.5g under pure ratio,
    vs 5g under pure 10%). The remaining 90% of daily carbs (45g) is reduced
    proportionally to compensate, keeping daily C=50g.
    """
    # Target macros from ratio (kcal-preserving)
    target_p_g = (slot_kcal * target_ratio_p) / 4.0
    target_c_g = (slot_kcal * target_ratio_c) / 4.0
    target_f_g = (slot_kcal * target_ratio_f) / 9.0
    # 50/50 blend: half from daily-macro-fraction, half from target ratio
    blended_p = (base_p_g + target_p_g) / 2.0
    blended_c = (base_c_g + target_c_g) / 2.0
    blended_f = (base_f_g + target_f_g) / 2.0
    # Clamp negatives (can occur if base macros exceed slot kcal, e.g. very
    # high-protein cut where 10% of daily protein alone exceeds 10% of kcal)
    blended_p = max(0.0, blended_p)
    blended_c = max(0.0, blended_c)
    blended_f = max(0.0, blended_f)
    return (blended_p, blended_c, blended_f)


def compute_post_workout_target(
    daily_kcal: float,
    daily_protein_g: float,
    daily_carb_g: float,
    daily_fat_g: float,
) -> MealSlotTarget:
    """
    Post-workout meal target — preserves daily macro totals (Phase-6 fix).

    Protein + carbs for recovery. ~15% of daily kcal, eaten 30-60 min after.

    Same approach as pre-workout: take 15% of daily macros, then re-allocate
    within the slot's kcal budget toward the post-workout ratio
    (35% P / 50% C / 15% F). Daily totals preserved.
    """
    slot_kcal = daily_kcal * 0.15
    base_p = daily_protein_g * 0.15
    base_c = daily_carb_g * 0.15
    base_f = daily_fat_g * 0.15
    target_p, target_c, target_f = _rebalance_slot_macros(
        slot_kcal, base_p, base_c, base_f, *POST_WORKOUT_MACRO_RATIO,
    )
    return MealSlotTarget(
        meal_type=MealType.POST_WORKOUT,
        target_kcal=slot_kcal,
        target_protein_g=target_p,
        target_carb_g=target_c,
        target_fat_g=target_f,
        target_fiber_g=4.0,
        is_training_day_slot=True,
        timing_note="30-60 min after workout",
    )


# === Per-meal allocation percentages ===

# Standard allocation (no pre/post workout)
STANDARD_ALLOCATIONS: dict[int, dict[MealType, float]] = {
    2: {  # IF 16:8 — 2 meals
        MealType.LUNCH: 0.45,
        MealType.DINNER: 0.55,
    },
    3: {  # default — 3 meals
        MealType.BREAKFAST: 0.30,
        MealType.LUNCH: 0.35,
        MealType.DINNER: 0.35,
    },
    4: {  # 3 meals + 1 snack
        MealType.BREAKFAST: 0.25,
        MealType.LUNCH: 0.30,
        MealType.DINNER: 0.30,
        MealType.SNACK: 0.15,
    },
    5: {  # 3 meals + 2 snacks — must sum to 1.0 (Tier 1.3 fix)
        MealType.BREAKFAST: 0.20,
        MealType.LUNCH: 0.25,
        MealType.DINNER: 0.25,
        MealType.SNACK: 0.30,   # split between 2 snacks → 0.15 each
        # Note: SNACK appears twice in template; allocator handles split
    },
}


def get_meal_allocation(
    meal_frequency: int,
    include_pre_post_workout: bool = False,
    is_training_day: bool = False,
) -> dict[MealType, float]:
    """
    Get the macro allocation percentages for a given meal frequency.

    If include_pre_post_workout=True AND is_training_day=True:
      - Pre-workout takes 10% of daily kcal
      - Post-workout takes 15% of daily kcal
      - Remaining 75% distributed across standard meals

    Returns dict {meal_type: pct_of_daily}.
    """
    if not include_pre_post_workout or not is_training_day:
        if meal_frequency not in STANDARD_ALLOCATIONS:
            meal_frequency = 3
        return STANDARD_ALLOCATIONS[meal_frequency].copy()

    # Training day with pre/post workout
    # Pre=10%, Post=15%, remaining 75% distributed
    if meal_frequency == 3:
        return {
            MealType.PRE_WORKOUT: 0.10,
            MealType.POST_WORKOUT: 0.15,
            MealType.BREAKFAST: 0.20,   # 0.75 * 0.27 ≈ 0.20
            MealType.LUNCH: 0.275,      # 0.75 * 0.37 ≈ 0.28
            MealType.DINNER: 0.275,
        }
    elif meal_frequency == 4:
        return {
            MealType.PRE_WORKOUT: 0.10,
            MealType.POST_WORKOUT: 0.15,
            MealType.BREAKFAST: 0.15,
            MealType.LUNCH: 0.225,
            MealType.DINNER: 0.225,
            MealType.SNACK: 0.15,
        }
    else:  # 5 meals — must sum to 1.0 (Tier 1.3 fix: was 0.90)
        return {
            MealType.PRE_WORKOUT: 0.10,
            MealType.POST_WORKOUT: 0.15,
            MealType.BREAKFAST: 0.15,
            MealType.LUNCH: 0.20,
            MealType.DINNER: 0.20,
            MealType.SNACK: 0.20,   # split between 2 snacks → 0.10 each
            # Note: in 5-meal template, SNACK appears twice → each gets 0.20/2 = 0.10
        }


# === Meal plan requirements (top-level) ===

@dataclass
class MealPlanRequirements:
    """Complete set of nutritional requirements for a meal plan."""
    # Daily totals
    daily_kcal: float
    daily_protein_g: float
    daily_carb_g: float
    daily_fat_g: float
    daily_fiber_g: float

    # Per-slot targets (list of MealSlotTarget, one per meal slot in the day)
    slot_targets: list[MealSlotTarget] = field(default_factory=list)

    # Training-day slot targets (includes PRE/POST workout)
    training_day_slot_targets: list[MealSlotTarget] = field(default_factory=list)

    # Configuration
    meal_frequency: int = 3
    include_pre_post_workout: bool = False
    training_days_per_week: int = 3
    # Phase-6 cleanup: removed ``training_time_of_day: str = "evening"`` field
    # — it was set but never read by any consumer (the actual training time
    # is read from ``profile.training_time_of_day`` at slot-construction time).

    # Diet + filtering
    diet_tag: str = "OMNI"
    cuisine_preference: Optional[str] = None
    allergens_to_avoid: list[str] = field(default_factory=list)
    excluded_ingredients: list[str] = field(default_factory=list)

    # Goal
    goal: str = "maintenance"

    # Notes
    notes: list[str] = field(default_factory=list)

    @property
    def total_slots_per_day(self) -> int:
        """Number of meal slots per non-training day."""
        return len(self.slot_targets)

    @property
    def total_slots_per_training_day(self) -> int:
        """Number of meal slots per training day (includes PRE/POST if enabled)."""
        return len(self.training_day_slot_targets) if self.training_day_slot_targets else len(self.slot_targets)


def compute_meal_plan_requirements(
    profile: UserProfile,
    assessment: AssessmentResult,
    nutrition: NutritionPlan,
    meal_frequency: int = 3,
    include_pre_post_workout: bool = False,
    cuisine_preference: Optional[str] = None,
    allergens_to_avoid: Optional[list[str]] = None,
    excluded_ingredients: Optional[list[str]] = None,
) -> MealPlanRequirements:
    """
    Compute the complete set of nutritional requirements for a meal plan.

    Args:
      profile: user profile
      assessment: assessment result
      nutrition: nutrition plan (provides daily kcal + macros)
      meal_frequency: 2-5 meals per day
      include_pre_post_workout: add PRE/POST workout slots on training days
      cuisine_preference: optional cuisine filter
      allergens_to_avoid: list of allergens to exclude
      excluded_ingredients: list of ingredients to exclude

    Returns MealPlanRequirements with per-slot targets.
    """
    if meal_frequency not in (2, 3, 4, 5):
        meal_frequency = 3

    macros = nutrition.macros
    daily_kcal = macros.protein_kcal + macros.fat_kcal + macros.carb_kcal
    daily_p = macros.protein_g
    daily_c = macros.carb_g
    daily_f = macros.fat_g
    daily_fiber = nutrition.micronutrients.fiber_g

    # === Standard day slot targets ===
    standard_alloc = get_meal_allocation(
        meal_frequency,
        include_pre_post_workout=False,
        is_training_day=False,
    )

    slot_targets: list[MealSlotTarget] = []
    # Handle 5-meal case (SNACK appears twice)
    if meal_frequency == 5:
        snack_pct = standard_alloc[MealType.SNACK] / 2
        template = [MealType.BREAKFAST, MealType.SNACK, MealType.LUNCH,
                    MealType.SNACK, MealType.DINNER]
        snack_count = 0
        for mt in template:
            if mt == MealType.SNACK:
                snack_count += 1
                pct = snack_pct
                slot_targets.append(_make_slot(
                    mt, pct, daily_kcal, daily_p, daily_c, daily_f, daily_fiber,
                    timing_note=f"snack {snack_count}",
                ))
            else:
                pct = standard_alloc[mt]
                slot_targets.append(_make_slot(
                    mt, pct, daily_kcal, daily_p, daily_c, daily_f, daily_fiber,
                ))
    else:
        for mt, pct in standard_alloc.items():
            slot_targets.append(_make_slot(
                mt, pct, daily_kcal, daily_p, daily_c, daily_f, daily_fiber,
            ))

    # === Training day slot targets (with PRE/POST workout) ===
    training_day_slot_targets: list[MealSlotTarget] = []
    if include_pre_post_workout:
        training_alloc = get_meal_allocation(
            meal_frequency,
            include_pre_post_workout=True,
            is_training_day=True,
        )

        # Pre/Post workout slots (Phase-6 fix: these now preserve daily macros
        # by blending 10%/15% of daily macros with the workout ratio).
        pre_target = compute_pre_workout_target(daily_kcal, daily_p, daily_c, daily_f)
        post_target = compute_post_workout_target(daily_kcal, daily_p, daily_c, daily_f)

        # Standard slots on training days must absorb the macro offset caused
        # by the PRE/POST ratio override. Compute the residual macros that the
        # standard slots need to deliver, then distribute proportionally to
        # each standard slot's kcal share.
        std_p_total = daily_p - pre_target.target_protein_g - post_target.target_protein_g
        std_c_total = daily_c - pre_target.target_carb_g - post_target.target_carb_g
        std_f_total = daily_f - pre_target.target_fat_g - post_target.target_fat_g
        std_kcal_total = daily_kcal - pre_target.target_kcal - post_target.target_kcal

        # Standard slots (minus the pre/post allocation)
        if meal_frequency == 5:
            snack_pct = training_alloc[MealType.SNACK] / 2
            template = [MealType.BREAKFAST, MealType.SNACK, MealType.LUNCH,
                        MealType.SNACK, MealType.DINNER]
            snack_count = 0
            for mt in template:
                if mt == MealType.SNACK:
                    snack_count += 1
                    pct = snack_pct
                    training_day_slot_targets.append(_make_residual_slot(
                        mt, pct, std_kcal_total, std_p_total, std_c_total, std_f_total,
                        daily_fiber, std_kcal_total,
                        timing_note=f"snack {snack_count}",
                    ))
                else:
                    pct = training_alloc[mt]
                    training_day_slot_targets.append(_make_residual_slot(
                        mt, pct, std_kcal_total, std_p_total, std_c_total, std_f_total,
                        daily_fiber, std_kcal_total,
                    ))
        else:
            for mt, pct in training_alloc.items():
                if mt in (MealType.PRE_WORKOUT, MealType.POST_WORKOUT):
                    continue   # handled separately
                training_day_slot_targets.append(_make_residual_slot(
                    mt, pct, std_kcal_total, std_p_total, std_c_total, std_f_total,
                    daily_fiber, std_kcal_total,
                ))

        # Insert PRE/POST at appropriate positions based on training_time_of_day.
        # Tier 3.38 fix: training_time_of_day is now a real field on UserProfile
        # (TrainingTimeOfDay enum). Previously this was a dead getattr that always
        # returned 'evening'. Now the morning/midday/evening branching actually fires.
        # Phase-6 cleanup: the field is always present with a default, so the
        # hasattr shim was unnecessary.
        training_time = profile.training_time_of_day.value
        if training_time == "morning":
            # PRE right after breakfast, POST as morning snack
            training_day_slot_targets.insert(0, pre_target)
            training_day_slot_targets.insert(1, post_target)
        elif training_time == "midday":
            # PRE before lunch, POST after lunch
            # Insert at position 1 (after breakfast, before lunch)
            insert_pos = 1
            training_day_slot_targets.insert(insert_pos, pre_target)
            training_day_slot_targets.insert(insert_pos + 2, post_target)
        else:  # evening (default)
            # PRE before dinner, POST after dinner
            training_day_slot_targets.append(pre_target)
            training_day_slot_targets.append(post_target)
    else:
        training_day_slot_targets = list(slot_targets)

    # === Diet tag ===
    diet_tag = get_recipe_diet_tag(profile.diet_type)
    # Override if cuisine_preference includes ethiopian
    if cuisine_preference and "ethiopian" in cuisine_preference.lower():
        if diet_tag == "VEGAN":
            diet_tag = "VEGAN_ETHIOPIAN"
        elif diet_tag == "OMNI":
            diet_tag = "OMNI_ETHIOPIAN"

    # === Goal mapping ===
    goal_map = {
        RecommendedStrategy.CUT: "cut",
        RecommendedStrategy.BULK: "bulk",
        RecommendedStrategy.RECOMP: "recomp",
        RecommendedStrategy.MAINTENANCE: "maintenance",
        RecommendedStrategy.HABIT_CHANGE_FIRST: "maintenance",
    }
    goal = goal_map.get(assessment.recommended_strategy, "maintenance")

    # === Notes ===
    notes = [
        f"Daily target: {daily_kcal:.0f} kcal, "
        f"P{daily_p:.0f}g / C{daily_c:.0f}g / F{daily_f:.0f}g / Fiber {daily_fiber:.0f}g",
        f"Meal frequency: {meal_frequency} meals/day"
        + (f" (+ PRE/POST workout on {profile.training_days_per_week} training days)"
           if include_pre_post_workout else ""),
        f"Diet: {diet_tag}"
        + (f", Cuisine: {cuisine_preference}" if cuisine_preference else ""),
    ]
    if allergens_to_avoid:
        notes.append(f"Allergens to avoid: {', '.join(allergens_to_avoid)}")
    if excluded_ingredients:
        notes.append(f"Excluded ingredients: {', '.join(excluded_ingredients)}")

    return MealPlanRequirements(
        daily_kcal=daily_kcal,
        daily_protein_g=daily_p,
        daily_carb_g=daily_c,
        daily_fat_g=daily_f,
        daily_fiber_g=daily_fiber,
        slot_targets=slot_targets,
        training_day_slot_targets=training_day_slot_targets,
        meal_frequency=meal_frequency,
        include_pre_post_workout=include_pre_post_workout,
        training_days_per_week=profile.training_days_per_week,
        # Phase-6 cleanup: ``training_time_of_day`` field removed from
        # MealPlanRequirements — was set but never read.
        diet_tag=diet_tag,
        cuisine_preference=cuisine_preference,
        allergens_to_avoid=allergens_to_avoid or [],
        excluded_ingredients=excluded_ingredients or [],
        goal=goal,
        notes=notes,
    )


def _make_slot(
    meal_type: MealType,
    pct: float,
    daily_kcal: float,
    daily_p: float,
    daily_c: float,
    daily_f: float,
    daily_fiber: float,
    timing_note: str = "",
) -> MealSlotTarget:
    """Build a MealSlotTarget from a percentage of daily targets."""
    return MealSlotTarget(
        meal_type=meal_type,
        target_kcal=daily_kcal * pct,
        target_protein_g=daily_p * pct,
        target_carb_g=daily_c * pct,
        target_fat_g=daily_f * pct,
        target_fiber_g=daily_fiber * pct,
        timing_note=timing_note,
    )


def _make_residual_slot(
    meal_type: MealType,
    pct: float,
    std_kcal_total: float,
    std_p_total: float,
    std_c_total: float,
    std_f_total: float,
    daily_fiber: float,
    std_kcal_for_pct: float,
    timing_note: str = "",
) -> MealSlotTarget:
    """
    Build a MealSlotTarget for a standard slot on a training day.

    The slot's kcal is `pct` of the standard-slot kcal budget (which excludes
    PRE/POST). The slot's macros are `pct` of the residual macros (daily
    macros minus what PRE/POST already took). This ensures that the sum of
    all training-day slots equals the daily macro targets exactly.

    Phase-6 fix: previously each standard slot used `pct * daily_p/c/f`, which
    double-counted the macros that PRE/POST already allocated — causing
    training-day totals to exceed daily targets whenever PRE/POST used a
    different macro ratio than the daily split.
    """
    # `pct` is expressed as a fraction of the standard slots' combined kcal
    # (std_kcal_for_pct), not of daily kcal. Convert to a fraction of std total.
    if std_kcal_for_pct <= 0:
        slot_kcal = 0.0
        fraction = 0.0
    else:
        slot_kcal = std_kcal_for_pct * pct
        fraction = pct   # pct is already a fraction of std_kcal_for_pct
    return MealSlotTarget(
        meal_type=meal_type,
        target_kcal=slot_kcal,
        target_protein_g=std_p_total * fraction,
        target_carb_g=std_c_total * fraction,
        target_fat_g=std_f_total * fraction,
        target_fiber_g=daily_fiber * fraction,
        timing_note=timing_note,
    )


__all__ = [
    "MealSlotTarget",
    "MealPlanRequirements",
    "compute_meal_plan_requirements",
    "compute_pre_workout_target",
    "compute_post_workout_target",
    "get_meal_allocation",
    "get_recipe_diet_tag",
    "STANDARD_ALLOCATIONS",
]
