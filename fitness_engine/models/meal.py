"""
Meal plan data models.

Phase-1: framework-ready. Ships with a minimal food database (~50 staples) and
7-day template scaffolding. The user will supply detailed meal resources later —
the food database and meal templates are designed for extension.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"


class FoodCategory(str, Enum):
    PROTEIN_ANIMAL = "protein_animal"
    PROTEIN_PLANT = "protein_plant"
    CARB_GRAIN = "carb_grain"
    CARB_STARCHY_VEG = "carb_starchy_veg"
    CARB_FRUIT = "carb_fruit"
    FAT_OIL = "fat_oil"
    FAT_NUT_SEED = "fat_nut_seed"
    DAIRY = "dairy"
    VEGETABLE = "vegetable"
    BEVERAGE = "beverage"
    CONDIMENT = "condiment"


@dataclass
class FoodItem:
    """Nutrition info per 100g of a food."""
    name: str
    category: FoodCategory
    kcal_per_100g: float
    protein_g_per_100g: float
    carb_g_per_100g: float
    fat_g_per_100g: float
    fiber_g_per_100g: float = 0.0
    serving_size_g: float = 100.0        # typical serving
    serving_description: str = "100 g"   # e.g., "1 medium apple"
    is_vegan: bool = False
    notes: str = ""


@dataclass
class MealFood:
    """A food item with a specific gram amount in a meal."""
    food: FoodItem
    grams: float

    @property
    def kcal(self) -> float:
        return self.food.kcal_per_100g * self.grams / 100

    @property
    def protein_g(self) -> float:
        return self.food.protein_g_per_100g * self.grams / 100

    @property
    def carb_g(self) -> float:
        return self.food.carb_g_per_100g * self.grams / 100

    @property
    def fat_g(self) -> float:
        return self.food.fat_g_per_100g * self.grams / 100


@dataclass
class Meal:
    """A single meal composed of multiple foods."""
    meal_type: MealType
    name: str
    foods: list[MealFood] = field(default_factory=list)
    target_kcal: float = 0.0
    target_protein_g: float = 0.0
    target_carb_g: float = 0.0
    target_fat_g: float = 0.0
    notes: str = ""

    @property
    def total_kcal(self) -> float:
        return sum(f.kcal for f in self.foods)

    @property
    def total_protein_g(self) -> float:
        return sum(f.protein_g for f in self.foods)

    @property
    def total_carb_g(self) -> float:
        return sum(f.carb_g for f in self.foods)

    @property
    def total_fat_g(self) -> float:
        return sum(f.fat_g for f in self.foods)


@dataclass
class DayPlan:
    """One day's worth of meals."""
    day_number: int                      # 1-7
    day_name: str                        # "Day 1", "Monday", etc.
    meals: list[Meal] = field(default_factory=list)

    @property
    def total_kcal(self) -> float:
        return sum(m.total_kcal for m in self.meals)

    @property
    def total_protein_g(self) -> float:
        return sum(m.total_protein_g for m in self.meals)

    @property
    def total_carb_g(self) -> float:
        return sum(m.total_carb_g for m in self.meals)

    @property
    def total_fat_g(self) -> float:
        return sum(m.total_fat_g for m in self.meals)


@dataclass
class MealPlan:
    """Top-level meal plan output — a 7-day template."""
    days: list[DayPlan] = field(default_factory=list)
    meal_frequency: int = 3              # 2-5 meals per day
    macro_allocation: dict = field(default_factory=dict)  # meal_type -> % of daily
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        def _convert(obj):
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _convert(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [_convert(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            return obj
        return _convert(self)


@dataclass
class FitnessPlan:
    """Top-level engine output combining all sub-plans."""
    nutrition: NutritionPlan
    training: TrainingPlan
    meal: MealPlan
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "nutrition": self.nutrition.to_dict(),
            "training": self.training.to_dict(),
            "meal": self.meal.to_dict(),
            "summary": self.summary,
        }


# Forward-import NutritionPlan & TrainingPlan to satisfy type hints
from .nutrition import NutritionPlan
from .training import TrainingPlan


__all__ = [
    "MealType",
    "FoodCategory",
    "FoodItem",
    "MealFood",
    "Meal",
    "DayPlan",
    "MealPlan",
    "FitnessPlan",
]
