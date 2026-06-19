"""
Meal plan generator — orchestrates meal frequency, macro allocation,
food selection, and 7-day template generation.

Phase-1: generates a 7-day meal plan with rotating food choices.
Future: integrate user-supplied meal resources for richer templates.
"""
from __future__ import annotations

from ..models.profile import UserProfile
from ..models.assessment import AssessmentResult
from ..models.nutrition import NutritionPlan, MacroSplit
from ..models.meal import (
    MealPlan, DayPlan, Meal, MealFood, MealType,
)
from .food_database import FOODS, get_food
from .meal_templates import get_meal_plan_template, get_meal_name
from .allocator import allocate_macros_per_meal, select_foods_for_meal


def build_meal_plan(
    profile: UserProfile,
    assessment: AssessmentResult,
    nutrition: NutritionPlan,
    meal_frequency: int = 3,
) -> MealPlan:
    """
    Build a 7-day meal plan template that hits the daily macro targets.

    Args:
      profile: user profile (used for diet_type, future vegan/keto support)
      assessment: assessment result
      nutrition: nutrition plan (provides macro targets)
      meal_frequency: 2-5 meals per day (default 3)

    Returns MealPlan with 7 DayPlans.
    """
    if meal_frequency not in (2, 3, 4, 5):
        meal_frequency = 3

    macros = nutrition.macros
    daily_kcal = macros.protein_kcal + macros.fat_kcal + macros.carb_kcal

    # Allocate macros per meal
    per_meal_targets = allocate_macros_per_meal(macros, meal_frequency)

    # Build 7 day plans
    days: list[DayPlan] = []
    day_names = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]

    meal_template = get_meal_plan_template(meal_frequency)

    for day_idx in range(7):
        day_num = day_idx + 1
        meals: list[Meal] = []

        # For 5-meal case, we have two SNACK entries; track index
        snack_count = 0

        for meal_type in meal_template:
            if meal_type == MealType.SNACK:
                snack_count += 1
                target_key = f"{meal_type.value}_{snack_count}" if meal_frequency == 5 else meal_type.value
            else:
                target_key = meal_type.value

            targets = per_meal_targets.get(target_key)
            if targets is None:
                continue

            # Select foods
            meal_foods = select_foods_for_meal(
                meal_type=meal_type,
                protein_target_g=targets["protein_g"],
                carb_target_g=targets["carb_g"],
                fat_target_g=targets["fat_g"],
                kcal_target=targets["kcal"],
                day=day_num,
            )

            meal_name = get_meal_name(meal_type, day_num)
            if meal_type == MealType.SNACK and meal_frequency == 5:
                meal_name = f"{meal_name} ({['morning','afternoon'][snack_count-1]})"

            meals.append(Meal(
                meal_type=meal_type,
                name=meal_name,
                foods=meal_foods,
                target_kcal=round(targets["kcal"], 0),
                target_protein_g=round(targets["protein_g"], 0),
                target_carb_g=round(targets["carb_g"], 0),
                target_fat_g=round(targets["fat_g"], 0),
                notes=f"Target: {targets['kcal']:.0f} kcal, "
                      f"P{targets['protein_g']:.0f}g/C{targets['carb_g']:.0f}g/"
                      f"F{targets['fat_g']:.0f}g",
            ))

        days.append(DayPlan(
            day_number=day_num,
            day_name=day_names[day_idx],
            meals=meals,
        ))

    # Compute macro allocation for reference
    from .meal_templates import get_meal_allocation
    allocation = get_meal_allocation(meal_frequency)

    notes = [
        f"Meal frequency: {meal_frequency} meals/day",
        f"Daily target: {daily_kcal:.0f} kcal, "
        f"P{macros.protein_g:.0f}g / C{macros.carb_g:.0f}g / F{macros.fat_g:.0f}g",
        "7-day rotating template — food choices vary daily for variety.",
        "Vegetables are 'free' (low calorie, high volume) — add liberally.",
        "Phase-1 framework: simple greedy allocator. Phase-2 will use "
        "optimization-based selection once detailed food database is loaded.",
        "Swap proteins: chicken ↔ turkey ↔ fish; carbs: rice ↔ potato ↔ pasta.",
    ]

    return MealPlan(
        days=days,
        meal_frequency=meal_frequency,
        macro_allocation={mt.value: pct for mt, pct in allocation.items()},
        notes=notes,
    )


__all__ = ["build_meal_plan"]
