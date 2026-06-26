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

from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.meal import MealType
from ..models.nutrition import NutritionPlan
from ..models.profile import (
    DietType,
    UserProfile,
)

# === Diet type mapping ===
# removed dead `DIET_TYPE_RECIPE_TAG` dict — it was defined but
# never used (get_recipe_diet_tag below uses its own substring logic). Keeping
# a second source of truth for the same mapping would invite drift.


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
    # Check for Ethiopian preference via profile.cuisine_preference or
    # via the diet_type itself. DietType is an Enum and always has ``.value``.
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
    daily_fiber_g: float = 0.0,
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

    v3.1.4 MEDIUM-4 fix: ``target_fiber_g`` is now derived proportionally from
    ``daily_fiber_g`` (capped at 2g) instead of being hardcoded to 2.0.
    Previously a user with daily_fiber=4g would get PRE+POST fiber = 6g
    (50% overshoot) while std slots got 0g via `max(0, residual)` clamping.
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
    # v3.1.4 MEDIUM-4: proportional fiber, capped at 2g. PRE takes 10% of
    # daily fiber (matching its 10% kcal share) but never exceeds 2g (PRE is
    # eaten 60-90 min pre-workout where high fiber causes GI distress).
    pre_fiber = min(2.0, daily_fiber_g * 0.10) if daily_fiber_g > 0 else 2.0
    return MealSlotTarget(
        meal_type=MealType.PRE_WORKOUT,
        target_kcal=slot_kcal,
        target_protein_g=target_p,
        target_carb_g=target_c,
        target_fat_g=target_f,
        target_fiber_g=pre_fiber,
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
    daily_fiber_g: float = 0.0,
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
    # v3.1.4 MEDIUM-4: proportional fiber, capped at 4g. POST takes 15% of
    # daily fiber (matching its 15% kcal share) but never exceeds 4g (POST is
    # eaten 30-60 min post-workout; fiber slows protein absorption which is
    # undesirable in the immediate recovery window).
    post_fiber = min(4.0, daily_fiber_g * 0.15) if daily_fiber_g > 0 else 4.0
    return MealSlotTarget(
        meal_type=MealType.POST_WORKOUT,
        target_kcal=slot_kcal,
        target_protein_g=target_p,
        target_carb_g=target_c,
        target_fat_g=target_f,
        target_fiber_g=post_fiber,
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
    5: {  # 3 meals + 2 snacks — must sum to 1.0
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
    else:  # 5 meals — must sum to 1.0
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
    # Diet + filtering
    diet_tag: str = "OMNI"
    cuisine_preference: str | None = None
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
    cuisine_preference: str | None = None,
    allergens_to_avoid: list[str] | None = None,
    excluded_ingredients: list[str] | None = None,
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
    slot_targets = _build_slot_list(
        meal_frequency, daily_kcal, daily_p, daily_c, daily_f, daily_fiber,
        training_day=False,
    )

    # === Training day slot targets (with PRE/POST workout) ===
    # ``_build_slot_list(..., training_day=True)`` builds the residual slots
    # (PRE/POST macros subtracted from daily totals, no PRE/POST in the list).
    # ``_insert_pre_post_slots`` then inserts PRE/POST at the right positions
    # based on ``training_time_of_day`` (declarative, no fragile index math).
    # The field is always present with a default (TrainingTimeOfDay enum),
    # so no hasattr shim is needed.
    if include_pre_post_workout:
        training_day_slot_targets = _build_slot_list(
            meal_frequency, daily_kcal, daily_p, daily_c, daily_f, daily_fiber,
            training_day=True,
        )
        pre_target = compute_pre_workout_target(daily_kcal, daily_p, daily_c, daily_f, daily_fiber)
        post_target = compute_post_workout_target(daily_kcal, daily_p, daily_c, daily_f, daily_fiber)
        training_day_slot_targets = _insert_pre_post_slots(
            training_day_slot_targets, pre_target, post_target,
            profile.training_time_of_day.value,
        )
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
        # ``training_time_of_day`` field removed from
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


# === Slot-list construction helpers (extracted from compute_meal_plan_requirements) ===


def _build_slots_from_alloc(
    alloc: dict[MealType, float],
    meal_frequency: int,
    make_slot,
) -> list[MealSlotTarget]:
    """Build a list of ``MealSlotTarget`` from an allocation dict.

    For ``meal_frequency == 5``, uses the explicit template
    ``[BREAKFAST, SNACK, LUNCH, SNACK, DINNER]`` with the SNACK percentage
    split in half (so each of the two snack slots gets half the SNACK
    allocation). For all other frequencies, iterates the alloc dict directly
    (insertion order is preserved).

    Args:
        alloc:          ``{MealType: pct_of_daily}`` — should already exclude
                        any slots the caller wants to handle separately (e.g.
                        PRE_WORKOUT / POST_WORKOUT, which are inserted by
                        ``_insert_pre_post_slots``).
        meal_frequency: 2 / 3 / 4 / 5
        make_slot:      ``callable(meal_type, pct, timing_note) -> MealSlotTarget``.
                        Lets the standard-day and training-day callers plug in
                        ``_make_slot`` (daily macros) or ``_make_residual_slot``
                        (residual macros) without duplicating the snack-loop.
    """
    slots: list[MealSlotTarget] = []
    # Wire-up fix: use meal_templates.get_meal_plan_template as the single
    # source of truth for the per-frequency meal-type ordering (was an inline
    # duplicate of the same template here, which had drifted from
    # meal_templates.MEAL_ORDER). For meal_frequency == 5, the template has
    # two SNACK entries; we split the SNACK allocation evenly between them.
    from .meal_templates import get_meal_plan_template
    template = get_meal_plan_template(meal_frequency)
    # Count snacks in the template so we can split the alloc evenly.
    snack_count_in_template = sum(1 for mt in template if mt == MealType.SNACK)
    snack_pct_each = (
        alloc[MealType.SNACK] / snack_count_in_template
        if snack_count_in_template > 0 and MealType.SNACK in alloc
        else 0.0
    )
    snack_seen = 0
    for mt in template:
        if mt == MealType.SNACK:
            snack_seen += 1
            slots.append(make_slot(mt, snack_pct_each, f"snack {snack_seen}"))
        else:
            slots.append(make_slot(mt, alloc.get(mt, 0.0), ""))
    return slots


def _build_slot_list(
    meal_frequency: int,
    daily_kcal: float,
    daily_p: float,
    daily_c: float,
    daily_f: float,
    daily_fiber: float,
    training_day: bool,
) -> list[MealSlotTarget]:
    """Build the list of standard meal slots (no PRE/POST) for one day.

    Consolidates the standard-day and training-day slot-construction paths
    that were previously duplicated inline in ``compute_meal_plan_requirements``.

    - ``training_day=False``: each slot's kcal/macros are a fraction of the
      daily totals via :func:`_make_slot`.
    - ``training_day=True``: PRE/POST workout targets are computed internally
      and their macro contribution is subtracted from the daily totals; each
      remaining slot then gets a fraction of the *residual* macros via
      :func:`_make_residual_slot`. PRE/POST themselves are NOT included in
      the returned list — the caller inserts them separately via
      :func:`_insert_pre_post_slots` so they can be positioned by time of day.

    Both branches route through :func:`_build_slots_from_alloc` so the
    5-meal snack-split template is shared.

    Args:
        meal_frequency: 2 / 3 / 4 / 5.
        daily_kcal/daily_p/daily_c/daily_f/daily_fiber: daily macro targets.
        training_day: if True, build residual slots (PRE/POST macros
            subtracted); if False, build standard fraction-of-daily slots.

    Returns:
        List of :class:`MealSlotTarget` objects (no PRE_WORKOUT / POST_WORKOUT).
    """
    if not training_day:
        standard_alloc = get_meal_allocation(
            meal_frequency,
            include_pre_post_workout=False,
            is_training_day=False,
        )
        return _build_slots_from_alloc(
            standard_alloc, meal_frequency,
            lambda mt, pct, timing: _make_slot(
                mt, pct, daily_kcal, daily_p, daily_c, daily_f, daily_fiber,
                timing_note=timing,
            ),
        )

    # Training day: compute PRE/POST to derive residual macros, then build
    # residual slots. PRE/POST themselves are returned separately by the
    # caller via ``_insert_pre_post_slots``.
    pre_target = compute_pre_workout_target(daily_kcal, daily_p, daily_c, daily_f, daily_fiber)
    post_target = compute_post_workout_target(daily_kcal, daily_p, daily_c, daily_f, daily_fiber)
    std_p_total = daily_p - pre_target.target_protein_g - post_target.target_protein_g
    std_c_total = daily_c - pre_target.target_carb_g - post_target.target_carb_g
    std_f_total = daily_f - pre_target.target_fat_g - post_target.target_fat_g
    std_kcal_total = daily_kcal - pre_target.target_kcal - post_target.target_kcal

    training_alloc_full = get_meal_allocation(
        meal_frequency,
        include_pre_post_workout=True,
        is_training_day=True,
    )
    # PRE/POST are positioned separately by ``_insert_pre_post_slots`` —
    # exclude them here so the standard-slot list contains only the slots
    # that absorb residual macros.
    training_alloc = {
        mt: pct for mt, pct in training_alloc_full.items()
        if mt not in (MealType.PRE_WORKOUT, MealType.POST_WORKOUT)
    }
    # CRITICAL FIX: normalize the standard-slot percentages so they sum to 1.0
    # (as fractions of the residual std budget, NOT of daily kcal).
    # `get_meal_allocation(..., is_training_day=True)` returns pcts that are
    # fractions of DAILY kcal (so the full dict including PRE/POST sums to 1.0).
    # After excluding PRE/POST, the remaining pcts sum to ~0.75 (e.g. for
    # meal_freq=3: B=0.20 + L=0.275 + D=0.275 = 0.75). The previous code passed
    # these un-normalized pcts to `_make_residual_slot`, which multiplied them
    # by `std_kcal_total` (already = 0.75 × daily_kcal). The result was that
    # standard slots received 0.75 × 0.75 = 0.5625 of daily_kcal, plus PRE/POST
    # 0.25, totalling 0.8125 of daily_kcal — an 18.75% deficit on every
    # training day. Normalizing here makes std slots sum to exactly
    # `std_kcal_total` (= daily_kcal - pre - post), so the day's slots sum to
    # exactly `daily_kcal`.
    #
    # ADDITIONAL FIX (meal_freq=2): the alloc dict may contain meal types that
    # aren't in the user's template (e.g. BREAKFAST and SNACK for an
    # intermittent-fasting user with only LUNCH+DINNER). The template-based
    # `_build_slots_from_alloc` iterates only the template meal types, so any
    # pct for non-template meals would be silently dropped — leaving the
    # remaining slots under-allocated. Filter the alloc to only template meals
    # BEFORE normalizing, so the kept pcts always sum to 1.0 after normalization.
    from .meal_templates import get_meal_plan_template
    template_meals = set(get_meal_plan_template(meal_frequency))
    training_alloc = {
        mt: pct for mt, pct in training_alloc.items() if mt in template_meals
    }
    std_pct_sum = sum(training_alloc.values())
    if std_pct_sum > 0:
        training_alloc = {
            mt: pct / std_pct_sum for mt, pct in training_alloc.items()
        }
    # Also account for PRE/POST fiber: subtract their (hardcoded) fiber from
    # the daily fiber budget so std slots get the residual fiber, matching the
    # kcal/protein/carb/fat residual treatment.
    pre_fiber = pre_target.target_fiber_g
    post_fiber = post_target.target_fiber_g
    std_fiber_total = max(0.0, daily_fiber - pre_fiber - post_fiber)
    return _build_slots_from_alloc(
        training_alloc, meal_frequency,
        lambda mt, pct, timing: _make_residual_slot(
            mt, pct, std_kcal_total, std_p_total, std_c_total, std_f_total,
            std_fiber_total, std_kcal_total, timing_note=timing,
        ),
    )


# === PRE/POST insertion by time-of-day (declarative) ===
#
# Maps ``training_time_of_day`` to a (pre_position, post_position) pair where
# each position is one of:
#   - "before_breakfast" / "after_breakfast"  (canonical 5-meal-day index 0 / 1)
#   - "before_lunch"      / "after_lunch"      (canonical 5-meal-day index 2 / 3)
#   - "before_dinner"     / "after_dinner"     (find-based: index of DINNER)
#   - "end"                                   (append at end of slot list)
#
# Canonical positions are absolute indices into the slot list (clamped
# implicitly by ``list.insert`` when they exceed ``len(slots)``). They let us
# express "PRE before lunch" as "after_breakfast" — which lands PRE between
# BREAKFAST and LUNCH for meal_freq=3, and at index 1 regardless of frequency
# (matching the legacy ``insert(1, pre)`` behavior for all frequencies).
#
# Find-based positions are used for DINNER because evening training should sit
# relative to the user's *actual* dinner slot, not a canonical position —
# e.g. a 2-meal IF user has only LUNCH+DINNER (no BREAKFAST), so "after_dinner"
# must locate DINNER dynamically.
_PRE_POST_POSITIONS: dict[str, tuple[str, str]] = {
    "morning": ("before_breakfast", "after_breakfast"),
    "midday":  ("after_breakfast",  "after_lunch"),
    "evening": ("before_dinner",    "after_dinner"),
}

# Canonical 5-meal-day indices for the absolute position names.
_CANONICAL_POSITIONS: dict[str, int] = {
    "before_breakfast": 0,
    "after_breakfast":  1,
    "before_lunch":     2,
    "after_lunch":      3,
}


def _resolve_pre_post_position(
    slots: list[MealSlotTarget], position: str,
) -> int:
    """Resolve a named pre/post position to an integer index into ``slots``.

    See the ``_PRE_POST_POSITIONS`` docstring for the semantics of each
    position name. Find-based positions locate the DINNER slot in the current
    list (and fall back to ``len(slots)`` — i.e. end-of-list — if DINNER is
    absent, matching the legacy ``next(..., len(slots))`` fallback).
    """
    if position in _CANONICAL_POSITIONS:
        return _CANONICAL_POSITIONS[position]
    if position == "before_dinner":
        return next(
            (i for i, s in enumerate(slots) if s.meal_type == MealType.DINNER),
            len(slots),
        )
    if position == "after_dinner":
        # ``slots`` here is the list AFTER PRE was already inserted, so the
        # DINNER index has shifted by +1 relative to the original — this is
        # what makes POST land immediately after DINNER (not after PRE).
        return next(
            (i for i, s in enumerate(slots) if s.meal_type == MealType.DINNER),
            len(slots),
        ) + 1
    if position == "end":
        return len(slots)
    raise ValueError(f"unknown pre/post position: {position!r}")


def _insert_pre_post_slots(
    slots: list[MealSlotTarget],
    pre_target: MealSlotTarget,
    post_target: MealSlotTarget,
    training_time: str,
) -> list[MealSlotTarget]:
    """Return a new slot list with PRE/POST workout slots inserted.

    Non-mutating: copies ``slots`` and inserts PRE first, then POST (with
    POST's position resolved against the post-PRE list so positions like
    ``"after_dinner"`` land one slot past DINNER — matching the legacy
    ``insert(idx, pre); insert(idx+2, post)`` behavior).

    Positions are looked up declaratively via :data:`_PRE_POST_POSITIONS`
    keyed on ``training_time`` (one of ``morning`` / ``midday`` / ``evening``).
    For morning training, PRE lands at index 0 ("before_breakfast") — i.e.
    fasted training puts PRE ahead of breakfast. Unknown ``training_time``
    values default to ``"evening"`` (matching the original code's else-branch).

    Args:
        slots:         standard-day slot list (no PRE/POST).
        pre_target:    PRE_WORKOUT slot target to insert.
        post_target:   POST_WORKOUT slot target to insert.
        training_time: ``profile.training_time_of_day.value`` (e.g. "morning").

    Returns:
        A new list with PRE/POST inserted at the correct positions.
    """
    pre_pos, post_pos = _PRE_POST_POSITIONS.get(
        training_time, _PRE_POST_POSITIONS["evening"],
    )
    new_slots = list(slots)
    new_slots.insert(_resolve_pre_post_position(new_slots, pre_pos), pre_target)
    new_slots.insert(_resolve_pre_post_position(new_slots, post_pos), post_target)
    return new_slots


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
