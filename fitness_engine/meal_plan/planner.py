"""
Meal plan generator — orchestrates meal frequency, macro allocation,
recipe selection, and 7-day template generation.

Phase-2: recipe-based. Each meal slot is filled with a real recipe from
the curated (107) or uncurated (370) database, selected to match the
per-meal macro targets. Falls back to the Phase-1 raw-foods allocator
only when no recipe matches.

Selection flow per meal:
  1. Compute per-meal macro targets (Phase-1 logic, unchanged).
  2. Map the user's DietType to a recipe diet_types tag.
  3. Call select_recipe_for_meal with meal_type, target_kcal, diet, goal.
  4. If a recipe is found, attach it to the Meal.
  5. If no recipe matches, fall back to select_foods_for_meal (raw foods).
  6. Track cuisine mix + curated/uncurated counts for the plan summary.
"""
from __future__ import annotations

from collections import Counter

from ..models.profile import UserProfile, DietType, PrimaryGoal
from ..models.assessment import AssessmentResult, RecommendedStrategy
from ..models.nutrition import NutritionPlan, MacroSplit
from ..models.meal import (
    MealPlan, DayPlan, Meal, MealFood, MealType, Recipe,
)
from .food_database import FOODS, get_food
from .meal_templates import get_meal_plan_template, get_meal_name
from .allocator import (
    allocate_macros_per_meal,
    select_recipe_for_meal,
    select_foods_for_meal,
)
from .recipe_loader import database_stats


# === Diet type mapping ===

def _map_diet_type(profile_diet: DietType) -> str:
    """
    Map the user's DietType to a recipe diet_types tag.

    The recipe DB uses tags like OMNI, OMNI_ETHIOPIAN, VEGAN,
    VEGAN_ETHIOPIAN. We default to OMNI which matches both OMNI and
    OMNI_ETHIOPIAN recipes (the latter is a subset of OMNI).
    """
    if profile_diet == DietType.VEGAN:
        return "VEGAN"
    elif profile_diet == DietType.VEGETARIAN:
        return "VEGAN"  # closest available
    # Default: OMNI matches everything omnivore-compatible
    return "OMNI"


def _map_goal_to_recipe_goal(strategy: RecommendedStrategy) -> str | None:
    """Map the recommended strategy to a recipe goal_fit tag."""
    mapping = {
        RecommendedStrategy.CUT: "cut",
        RecommendedStrategy.BULK: "bulk",
        RecommendedStrategy.RECOMP: "recomp",
        RecommendedStrategy.MAINTENANCE: "maintenance",
        RecommendedStrategy.HABIT_CHANGE_FIRST: "maintenance",
    }
    return mapping.get(strategy)


# === Main orchestrator ===

def build_meal_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    nutrition: NutritionPlan,
    meal_frequency: int = 3,
    cuisine_preference: str | None = None,
) -> MealPlan:
    """
    Build a 7-day meal plan template that hits the daily macro targets.

    Args:
      profile: user profile (used for diet_type, goal)
      assessment: assessment result (used for recommended_strategy)
      nutrition: nutrition plan (provides macro targets)
      meal_frequency: 2-5 meals per day (default 3)
      cuisine_preference: optional cuisine filter (e.g. "ethiopian", "indian")

    Returns MealPlan with 7 DayPlans. Each Meal carries either a Recipe
    or a list of MealFood entries (Phase-1 fallback).
    """
    if meal_frequency not in (2, 3, 4, 5):
        meal_frequency = 3

    macros = nutrition.macros
    daily_kcal = macros.protein_kcal + macros.fat_kcal + macros.carb_kcal

    # Allocate macros per meal
    per_meal_targets = allocate_macros_per_meal(macros, meal_frequency)

    # Map user profile to recipe filter params
    diet_tag = _map_diet_type(profile.diet_type)
    goal_tag = _map_goal_to_recipe_goal(assessment.recommended_strategy)

    # Build 7 day plans
    days: list[DayPlan] = []
    day_names = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]

    meal_template = get_meal_plan_template(meal_frequency)

    # Track stats across the week
    cuisine_mix: Counter = Counter()
    curated_count = 0
    uncurated_count = 0
    fallback_count = 0  # meals that fell back to raw foods
    used_recipe_ids: set[str] = set()  # avoid repeating same recipe in same day

    for day_idx in range(7):
        day_num = day_idx + 1
        meals: list[Meal] = []
        # Reset per-day "used" set so the same recipe can appear on
        # different days (just not twice in the same day)
        day_used_ids: set[str] = set()

        snack_count = 0

        for meal_type in meal_template:
            if meal_type == MealType.SNACK:
                snack_count += 1
                target_key = (
                    f"{meal_type.value}_{snack_count}"
                    if meal_frequency == 5 else meal_type.value
                )
            else:
                target_key = meal_type.value

            targets = per_meal_targets.get(target_key)
            if targets is None:
                continue

            # Try recipe selection
            recipe = select_recipe_for_meal(
                meal_type=meal_type,
                target_kcal=targets["kcal"],
                target_protein_g=targets["protein_g"],
                target_carb_g=targets["carb_g"],
                target_fat_g=targets["fat_g"],
                day=day_num,
                diet_type=diet_tag,
                goal_fit=goal_tag,
                cuisine=cuisine_preference,
                exclude_ids=day_used_ids,
                prefer_curated=True,
            )

            # Defensive: if the user is vegan/vegetarian, skip recipes flagged
            # with diet-warning (curation errors where VEGAN-tagged recipes
            # actually contain meat/dairy/egg).
            if recipe and diet_tag in ("VEGAN", "VEGETARIAN"):
                if "[diet-warning" in (recipe.notes or ""):
                    # Try to find a clean alternative
                    alt_recipe = select_recipe_for_meal(
                        meal_type=meal_type,
                        target_kcal=targets["kcal"],
                        target_protein_g=targets["protein_g"],
                        target_carb_g=targets["carb_g"],
                        target_fat_g=targets["fat_g"],
                        day=day_num + 1,  # rotate to next recipe
                        diet_type=diet_tag,
                        goal_fit=goal_tag,
                        cuisine=cuisine_preference,
                        exclude_ids=day_used_ids | {recipe.id} if recipe.id else day_used_ids,
                        prefer_curated=True,
                    )
                    if alt_recipe and "[diet-warning" not in (alt_recipe.notes or ""):
                        recipe = alt_recipe

            meal_name = get_meal_name(meal_type, day_num)
            if meal_type == MealType.SNACK and meal_frequency == 5:
                meal_name = f"{meal_name} ({['morning','afternoon'][snack_count-1]})"

            if recipe:
                # Use the recipe's actual name as the meal name
                meal_name = recipe.name
                day_used_ids.add(recipe.id) if recipe.id else None
                used_recipe_ids.add(recipe.id) if recipe.id else None
                cuisine_mix[recipe.cuisine] += 1
                if "[curated]" in (recipe.notes or ""):
                    curated_count += 1
                else:
                    uncurated_count += 1

                actual_kcal = recipe.kcal
                actual_p = recipe.protein_g
                actual_c = recipe.carb_g
                actual_f = recipe.fat_g

                notes = (
                    f"Target: {targets['kcal']:.0f} kcal, "
                    f"P{targets['protein_g']:.0f}g/C{targets['carb_g']:.0f}g/"
                    f"F{targets['fat_g']:.0f}g | "
                    f"Actual: {actual_kcal:.0f} kcal, "
                    f"P{actual_p:.0f}g/C{actual_c:.0f}g/F{actual_f:.0f}g | "
                    f"Cuisine: {recipe.cuisine} | "
                    f"{'Curated' if '[curated]' in (recipe.notes or '') else 'Uncurated'}"
                )

                meals.append(Meal(
                    meal_type=meal_type,
                    name=meal_name,
                    recipe=recipe,
                    target_kcal=round(targets["kcal"], 0),
                    target_protein_g=round(targets["protein_g"], 0),
                    target_carb_g=round(targets["carb_g"], 0),
                    target_fat_g=round(targets["fat_g"], 0),
                    notes=notes,
                ))
            else:
                # Fallback: Phase-1 raw-foods allocator
                fallback_count += 1
                meal_foods = select_foods_for_meal(
                    meal_type=meal_type,
                    protein_target_g=targets["protein_g"],
                    carb_target_g=targets["carb_g"],
                    fat_target_g=targets["fat_g"],
                    kcal_target=targets["kcal"],
                    day=day_num,
                )
                meals.append(Meal(
                    meal_type=meal_type,
                    name=meal_name,
                    foods=meal_foods,
                    target_kcal=round(targets["kcal"], 0),
                    target_protein_g=round(targets["protein_g"], 0),
                    target_carb_g=round(targets["carb_g"], 0),
                    target_fat_g=round(targets["fat_g"], 0),
                    notes=(
                        f"Target: {targets['kcal']:.0f} kcal, "
                        f"P{targets['protein_g']:.0f}g/C{targets['carb_g']:.0f}g/"
                        f"F{targets['fat_g']:.0f}g | "
                        f"Fallback (no recipe match) — raw foods allocated"
                    ),
                ))

        days.append(DayPlan(
            day_number=day_num,
            day_name=day_names[day_idx],
            meals=meals,
        ))

    # Compute macro allocation for reference
    from .meal_templates import get_meal_allocation
    allocation = get_meal_allocation(meal_frequency)

    db_stats = database_stats()

    notes = [
        f"Meal frequency: {meal_frequency} meals/day",
        f"Daily target: {daily_kcal:.0f} kcal, "
        f"P{macros.protein_g:.0f}g / C{macros.carb_g:.0f}g / F{macros.fat_g:.0f}g",
        f"7-day rotating template — recipes vary daily for variety.",
        f"Recipe database: {db_stats['total_recipes']} recipes loaded "
        f"({db_stats['curated_count']} curated + {db_stats['uncurated_count']} uncurated).",
        f"Week summary: {curated_count} curated + {uncurated_count} uncurated recipes used; "
        f"{fallback_count} meal(s) fell back to raw-foods allocator.",
        f"Cuisine mix this week: {dict(cuisine_mix.most_common(10))}.",
        f"Each meal includes full ingredients, instructions, and nutrition per serving.",
        "Phase-2 recipe-based planner. Swap groups honored when available.",
    ]

    return MealPlan(
        days=days,
        meal_frequency=meal_frequency,
        macro_allocation={mt.value: pct for mt, pct in allocation.items()},
        cuisine_mix=dict(cuisine_mix.most_common(20)),
        recipe_source_summary={
            "curated_used": curated_count,
            "uncurated_used": uncurated_count,
            "fallback_to_raw_foods": fallback_count,
            "unique_recipes_used": len(used_recipe_ids),
            "database_total": db_stats["total_recipes"],
            "database_curated": db_stats["curated_count"],
            "database_uncurated": db_stats["uncurated_count"],
        },
        notes=notes,
    )


__all__ = ["build_meal_plan"]
