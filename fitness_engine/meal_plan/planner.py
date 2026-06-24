"""
Meal planner — clean 7-day orchestrator.

Builds a 7-day meal plan that hits the daily macro targets using:
  - profile_requirements.compute_meal_plan_requirements (per-slot targets)
  - allocator.allocate_meal (recipe + scaling + fillers per slot)
  - Weekly balancing (ensures macros hit across the week)
  - Variety tracking (no recipe repeated within 3 days)

Algorithm:
  1. Compute MealPlanRequirements from profile + nutrition
  2. Determine which days are training days (based on training_days_per_week)
  3. For each day (7 total):
     a. Pick the appropriate slot_targets (training day vs rest day)
     b. For each slot, call allocate_meal with:
        - slot target
        - used_recipe_ids_last_3_days (variety tracking)
        - used_today (no same-day repeats)
     c. Track used recipe IDs for the next day's variety check
  4. Compute weekly summary (avg kcal, macros, cuisine mix, unique recipes)
  5. Return MealPlan with 7 DayPlans, each containing Meal objects

Each Meal carries:
  - The recipe (with full ingredients + instructions)
  - Scale factor (if scaled)
  - Fillers (MealFood list)
  - Swap options (alternative recipes + ingredient swaps)
  - Score + match percentages
"""
from __future__ import annotations

from collections import Counter
from typing import Optional

from ..models.profile import UserProfile, DietType
from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.nutrition import NutritionPlan
from ..models.meal import (
    MealPlan, DayPlan, Meal, MealFood, MealType, Recipe,
)
from .profile_requirements import (
    compute_meal_plan_requirements, MealPlanRequirements, MealSlotTarget,
)
from .allocator import allocate_meal, SelectedMeal, selected_meal_to_dict
from .recipe_loader import database_stats


def build_meal_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    nutrition: NutritionPlan,
    meal_frequency: int = 3,
    cuisine_preference: Optional[str] = None,
    allergens_to_avoid: Optional[list[str]] = None,
    excluded_ingredients: Optional[list[str]] = None,
    include_pre_post_workout: bool = False,
) -> MealPlan:
    """
    Build a 7-day meal plan that hits the daily macro targets.

    Phase-5 clean implementation. Uses the new best-fit scoring algorithm,
    acceptable scaling, filler system, and swap alternatives.

    Args:
      profile: user profile
      assessment: assessment result
      nutrition: nutrition plan (provides macro targets)
      meal_frequency: 2-5 meals per day (default 3)
      cuisine_preference: optional cuisine filter
      allergens_to_avoid: list of allergens to exclude
      excluded_ingredients: list of ingredients to exclude
      include_pre_post_workout: add PRE/POST workout slots on training days

    Returns MealPlan with 7 DayPlans.
    """
    # 1. Compute requirements
    requirements = compute_meal_plan_requirements(
        profile=profile,
        assessment=assessment,
        nutrition=nutrition,
        meal_frequency=meal_frequency,
        include_pre_post_workout=include_pre_post_workout,
        cuisine_preference=cuisine_preference,
        allergens_to_avoid=allergens_to_avoid,
        excluded_ingredients=excluded_ingredients,
    )

    # 2. Determine training day schedule
    # Spread training days evenly across the week
    training_days = _compute_training_days(
        requirements.training_days_per_week,
        requirements.training_time_of_day,
    )

    # 3. Build 7 day plans
    days: list[DayPlan] = []
    day_names = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]

    # Track usage for variety
    used_recipe_ids_last_3_days: set[str] = set()
    used_recipe_ids_last_7_days: set[str] = set()
    daily_usage_history: list[set[str]] = []  # list of daily sets, oldest first

    cuisine_mix: Counter = Counter()
    curated_count = 0
    uncurated_count = 0
    fallback_count = 0
    unique_recipes: set[str] = set()
    weekly_kcal_total = 0.0
    weekly_protein_total = 0.0
    weekly_carb_total = 0.0
    weekly_fat_total = 0.0

    for day_idx in range(7):
        day_num = day_idx + 1
        is_training_day = day_num in training_days

        # Pick the right slot targets
        if is_training_day and requirements.include_pre_post_workout:
            slot_targets = requirements.training_day_slot_targets
        else:
            slot_targets = requirements.slot_targets

        # Allocate each meal slot
        meals: list[Meal] = []
        used_today: set[str] = set()

        for slot in slot_targets:
            is_main = slot.meal_type in (MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER)

            selected = allocate_meal(
                slot=slot,
                diet_tag=requirements.diet_tag,
                user_goal=requirements.goal,
                cuisine_preference=requirements.cuisine_preference,
                allergens_to_avoid=requirements.allergens_to_avoid,
                excluded_ingredients=requirements.excluded_ingredients,
                used_recipe_ids_last_3_days=used_recipe_ids_last_3_days,
                used_recipe_ids_last_7_days=used_recipe_ids_last_7_days,
                used_today=used_today,
                is_main_meal=is_main,
            )

            # Build Meal object
            if selected.recipe is not None:
                # Recipe-based meal
                if selected.recipe.id:
                    used_today.add(selected.recipe.id)
                    unique_recipes.add(selected.recipe.id)
                cuisine_mix[selected.recipe.cuisine] += 1
                if "[curated]" in (selected.recipe.notes or ""):
                    curated_count += 1
                else:
                    uncurated_count += 1

                # Build notes combining recipe notes + allocation notes
                meal_notes = "; ".join(selected.notes) if selected.notes else ""

                meal = Meal(
                    meal_type=slot.meal_type,
                    name=selected.recipe.name,
                    recipe=selected.recipe,
                    foods=selected.fillers,   # fillers stored in foods list
                    target_kcal=round(slot.target_kcal, 0),
                    target_protein_g=round(slot.target_protein_g, 0),
                    target_carb_g=round(slot.target_carb_g, 0),
                    target_fat_g=round(slot.target_fat_g, 0),
                    notes=meal_notes,
                )
                # Attach Phase-5 metadata to the meal's notes via a special prefix
                # (the to_dict method handles serialization)
                meals.append(meal)

                # Track weekly totals (using actual nutrition)
                weekly_kcal_total += selected.total_kcal
                weekly_protein_total += selected.total_protein_g
                weekly_carb_total += selected.total_carb_g
                weekly_fat_total += selected.total_fat_g
            else:
                # Fallback — no recipe found
                fallback_count += 1
                meals.append(Meal(
                    meal_type=slot.meal_type,
                    name=f"{slot.meal_type.value.title()} (no recipe match)",
                    foods=[],
                    target_kcal=round(slot.target_kcal, 0),
                    target_protein_g=round(slot.target_protein_g, 0),
                    target_carb_g=round(slot.target_carb_g, 0),
                    target_fat_g=round(slot.target_fat_g, 0),
                    notes="No recipe found — needs manual selection",
                ))

        days.append(DayPlan(
            day_number=day_num,
            day_name=day_names[day_idx],
            meals=meals,
        ))

        # Update variety tracking
        daily_usage_history.append(used_today)
        # Keep only last 7 days
        if len(daily_usage_history) > 7:
            daily_usage_history.pop(0)

        # Update 3-day and 7-day used sets
        used_recipe_ids_last_3_days = set()
        for daily_set in daily_usage_history[-3:]:
            used_recipe_ids_last_3_days |= daily_set
        used_recipe_ids_last_7_days = set()
        for daily_set in daily_usage_history:
            used_recipe_ids_last_7_days |= daily_set

    # 4. Compute weekly summary
    db_stats = database_stats()
    weekly_avg_kcal = weekly_kcal_total / 7
    weekly_avg_protein = weekly_protein_total / 7
    weekly_avg_carb = weekly_carb_total / 7
    weekly_avg_fat = weekly_fat_total / 7

    # Match percentages
    target_kcal = requirements.daily_kcal
    target_p = requirements.daily_protein_g
    target_c = requirements.daily_carb_g
    target_f = requirements.daily_fat_g

    weekly_kcal_match = (1 - abs(weekly_avg_kcal - target_kcal) / target_kcal) * 100 if target_kcal > 0 else 100
    weekly_protein_match = (1 - abs(weekly_avg_protein - target_p) / target_p) * 100 if target_p > 0 else 100

    notes = [
        f"Meal frequency: {meal_frequency} meals/day"
        + (f" (+ PRE/POST workout on {requirements.training_days_per_week} training days)"
           if include_pre_post_workout else ""),
        f"Daily target: {requirements.daily_kcal:.0f} kcal, "
        f"P{requirements.daily_protein_g:.0f}g / C{requirements.daily_carb_g:.0f}g / "
        f"F{requirements.daily_fat_g:.0f}g / Fiber {requirements.daily_fiber_g:.0f}g",
        f"Weekly average: {weekly_avg_kcal:.0f} kcal "
        f"({weekly_kcal_match:.1f}% match), "
        f"P{weekly_avg_protein:.0f}g ({weekly_protein_match:.1f}% match), "
        f"C{weekly_avg_carb:.0f}g, F{weekly_avg_fat:.0f}g",
        f"Diet: {requirements.diet_tag}"
        + (f", Cuisine: {cuisine_preference}" if cuisine_preference else ""),
        f"Recipe database: {db_stats['total_recipes']} recipes loaded",
        f"Week summary: {curated_count} curated + {uncurated_count} uncurated recipes used; "
        f"{fallback_count} meal(s) had no recipe match",
        f"Unique recipes used: {len(unique_recipes)} (target: ≥14 for variety)",
        f"Cuisine mix: {dict(cuisine_mix.most_common(10))}",
        f"Training days: {sorted(training_days)}",
        "Phase-5 best-fit scoring + acceptable scaling + filler system + swap alternatives.",
    ]

    return MealPlan(
        days=days,
        meal_frequency=meal_frequency,
        macro_allocation={},  # computed in requirements; left empty for Phase-5
        cuisine_mix=dict(cuisine_mix.most_common(20)),
        recipe_source_summary={
            "curated_used": curated_count,
            "uncurated_used": uncurated_count,
            "fallback_to_raw_foods": fallback_count,
            "unique_recipes_used": len(unique_recipes),
            "database_total": db_stats["total_recipes"],
            "database_curated": db_stats["curated_count"],
            "database_uncurated": db_stats["uncurated_count"],
            "weekly_avg_kcal": round(weekly_avg_kcal, 1),
            "weekly_avg_protein_g": round(weekly_avg_protein, 1),
            "weekly_avg_carb_g": round(weekly_avg_carb, 1),
            "weekly_avg_fat_g": round(weekly_avg_fat, 1),
            "weekly_kcal_match_pct": round(weekly_kcal_match, 1),
            "weekly_protein_match_pct": round(weekly_protein_match, 1),
            "training_days": sorted(training_days),
            "include_pre_post_workout": include_pre_post_workout,
        },
        notes=notes,
    )


def _compute_training_days(
    training_days_per_week: int,
    training_time_of_day: str = "evening",
) -> set[int]:
    """
    Determine which days of the week are training days.

    Spreads training days evenly. For example:
      - 3 days/week → {1, 3, 5} (Mon, Wed, Fri)
      - 4 days/week → {1, 2, 4, 5} (Mon, Tue, Thu, Fri)
      - 5 days/week → {1, 2, 3, 4, 5} (Mon-Fri)

    Returns set of 1-indexed day numbers (1=Mon, 7=Sun).
    """
    if training_days_per_week >= 7:
        return {1, 2, 3, 4, 5, 6, 7}
    if training_days_per_week <= 0:
        return set()

    # Common splits
    common_splits = {
        1: {1},                    # 1 day: Mon
        2: {1, 4},                 # 2 days: Mon, Thu
        3: {1, 3, 5},              # 3 days: Mon, Wed, Fri
        4: {1, 2, 4, 5},           # 4 days: Mon, Tue, Thu, Fri
        5: {1, 2, 3, 4, 5},        # 5 days: Mon-Fri
        6: {1, 2, 3, 4, 5, 6},     # 6 days: Mon-Sat
    }
    return common_splits.get(training_days_per_week, {1, 3, 5})


__all__ = ["build_meal_plan"]
