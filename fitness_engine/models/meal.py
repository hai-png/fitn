"""
Meal plan data models.

Phase-2: supports BOTH raw food items (FoodItem, for backward compat) AND
real recipes (Recipe, loaded from recipe_database.json +
recipe_database_uncurated.json).

The Meal dataclass now carries an optional `recipe` field. When set, the
meal is recipe-based (one cohesive dish with ingredients + instructions);
when None, the meal falls back to the Phase-1 raw-foods approach.
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
    SIDE = "side"
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


class DietType(str, Enum):
    """Recipe diet_type tags (subset of Phase-1 DietType, expanded)."""
    OMNI = "OMNI"
    OMNI_ETHIOPIAN = "OMNI_ETHIOPIAN"
    VEGAN = "VEGAN"
    VEGAN_ETHIOPIAN = "VEGAN_ETHIOPIAN"
    VEGETARIAN = "VEGETARIAN"


class GoalFit(str, Enum):
    """Recipe goal_fit tags."""
    CUT = "cut"
    BULK = "bulk"
    RECOMP = "recomp"
    MAINTENANCE = "maintenance"


class ProteinDensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CalorieDensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecipeKind(str, Enum):
    MEAL = "meal"
    PANTRY = "pantry"


# === Phase-1 raw food model (kept for backward compat) ===

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

    @property
    def fiber_g(self) -> float:
        """Fiber grams (Phase-5: needed for filler tracking)."""
        return getattr(self.food, 'fiber_g_per_100g', 0.0) * self.grams / 100


# === Phase-2 Recipe model ===

@dataclass
class NutritionPerServing:
    """Macros per single serving of a recipe."""
    kcal: float = 0.0
    protein_g: float = 0.0
    carb_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    sugar_g: float = 0.0


@dataclass
class Recipe:
    """
    A real recipe with ingredients, instructions, and per-serving nutrition.

    Loaded from fitness_engine/meal_plan/recipe_database.json (curated)
    or recipe_database_uncurated.json (broader pool).
    """
    # === Identity ===
    name: str
    id: Optional[str] = None               # e.g. "R001"
    source: Optional[str] = None            # URL
    source_file: Optional[str] = None
    legacy_id: Optional[str] = None

    # === Classification ===
    cuisine: str = "american"
    category: str = ""                      # free-text: "dinner, main, main course"
    recipe_kind: str = "meal"               # "meal" or "pantry"
    meal_types: list[str] = field(default_factory=list)   # ["breakfast", "lunch", ...]
    diet_types: list[str] = field(default_factory=list)   # ["OMNI", "VEGAN", ...]
    goal_fit: list[str] = field(default_factory=list)     # ["maintenance", "cut", ...]

    # === Servings & timing ===
    servings: int = 1
    prep_time_min: Optional[int] = None
    cook_time_min: Optional[int] = None

    # === Content ===
    ingredients: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)

    # === Nutrition (per serving) ===
    nutrition_per_serving: NutritionPerServing = field(default_factory=NutritionPerServing)
    nutrition_source: str = "published"    # "published" or "estimated"
    serving_size_g: Optional[float] = None

    # === Quality / density tags ===
    protein_density: Optional[str] = None  # "low" / "medium" / "high"
    calorie_density: Optional[str] = None  # "low" / "medium" / "high"
    allergens: list[str] = field(default_factory=list)
    alternative_recipe_ids: list[str] = field(default_factory=list)

    # === Cultural flags (Ethiopian cuisine specific) ===
    fasting_yetsom: bool = False            # Ethiopian Orthodox fasting-friendly
    injera_accompaniment: bool = False      # served with injera

    # === Media ===
    image_url: Optional[str] = None

    # === Misc ===
    notes: str = ""
    _extraction_method: Optional[str] = None

    @property
    def total_time_min(self) -> Optional[int]:
        """Total prep + cook time, or None if either is missing."""
        if self.prep_time_min is None or self.cook_time_min is None:
            return None
        return self.prep_time_min + self.cook_time_min

    @property
    def is_vegan(self) -> bool:
        return any(d.upper() == "VEGAN" for d in self.diet_types)

    @property
    def is_ethiopian(self) -> bool:
        return (
            "ethiopian" in self.cuisine.lower()
            or any("ETHIOPIAN" in d for d in self.diet_types)
        )

    @property
    def kcal(self) -> float:
        return self.nutrition_per_serving.kcal

    @property
    def protein_g(self) -> float:
        return self.nutrition_per_serving.protein_g

    @property
    def carb_g(self) -> float:
        return self.nutrition_per_serving.carb_g

    @property
    def fat_g(self) -> float:
        return self.nutrition_per_serving.fat_g

    @property
    def fiber_g(self) -> float:
        return self.nutrition_per_serving.fiber_g

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# === Meal / Day / Plan ===

@dataclass
class Meal:
    """
    A single meal.

    Phase-2 supports two modes:
      1. Recipe-based: `recipe` is set; `foods` is empty. The meal is a
         single cohesive dish (e.g. "Chechebsa") with full ingredients +
         instructions.
      2. Raw-foods-based (Phase-1 fallback): `recipe` is None; `foods` is
         populated with MealFood entries.

    Both modes carry target macros (the planner's per-meal allocation)
    and the actual macros of whatever was selected.
    """
    meal_type: MealType
    name: str
    foods: list[MealFood] = field(default_factory=list)
    recipe: Optional[Recipe] = None
    target_kcal: float = 0.0
    target_protein_g: float = 0.0
    target_carb_g: float = 0.0
    target_fat_g: float = 0.0
    notes: str = ""

    @property
    def total_kcal(self) -> float:
        if self.recipe:
            return self.recipe.kcal
        return sum(f.kcal for f in self.foods)

    @property
    def total_protein_g(self) -> float:
        if self.recipe:
            return self.recipe.protein_g
        return sum(f.protein_g for f in self.foods)

    @property
    def total_carb_g(self) -> float:
        if self.recipe:
            return self.recipe.carb_g
        return sum(f.carb_g for f in self.foods)

    @property
    def total_fat_g(self) -> float:
        if self.recipe:
            return self.recipe.fat_g
        return sum(f.fat_g for f in self.foods)

    def to_dict(self) -> dict:
        return {
            "meal_type": self.meal_type.value if isinstance(self.meal_type, MealType) else self.meal_type,
            "name": self.name,
            "recipe": self.recipe.to_dict() if self.recipe else None,
            "foods": [
                {
                    "food": {
                        "name": f.food.name,
                        "category": f.food.category.value if isinstance(f.food.category, FoodCategory) else f.food.category,
                        "kcal_per_100g": f.food.kcal_per_100g,
                        "protein_g_per_100g": f.food.protein_g_per_100g,
                        "carb_g_per_100g": f.food.carb_g_per_100g,
                        "fat_g_per_100g": f.food.fat_g_per_100g,
                        "fiber_g_per_100g": f.food.fiber_g_per_100g,
                        "serving_size_g": f.food.serving_size_g,
                        "serving_description": f.food.serving_description,
                        "is_vegan": f.food.is_vegan,
                    },
                    "grams": f.grams,
                }
                for f in self.foods
            ],
            "target_kcal": self.target_kcal,
            "target_protein_g": self.target_protein_g,
            "target_carb_g": self.target_carb_g,
            "target_fat_g": self.target_fat_g,
            "actual_kcal": self.total_kcal,
            "actual_protein_g": self.total_protein_g,
            "actual_carb_g": self.total_carb_g,
            "actual_fat_g": self.total_fat_g,
            "notes": self.notes,
        }


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

    def to_dict(self) -> dict:
        return {
            "day_number": self.day_number,
            "day_name": self.day_name,
            "meals": [m.to_dict() for m in self.meals],
            "total_kcal": self.total_kcal,
            "total_protein_g": self.total_protein_g,
            "total_carb_g": self.total_carb_g,
            "total_fat_g": self.total_fat_g,
        }


@dataclass
class MealPlan:
    """Top-level meal plan output — a 7-day template."""
    days: list[DayPlan] = field(default_factory=list)
    meal_frequency: int = 3              # 2-5 meals per day
    macro_allocation: dict = field(default_factory=dict)  # meal_type -> % of daily
    cuisine_mix: dict = field(default_factory=dict)       # cuisine -> count
    recipe_source_summary: dict = field(default_factory=dict)  # {"curated": N, "uncurated": M}
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "days": [d.to_dict() for d in self.days],
            "meal_frequency": self.meal_frequency,
            "macro_allocation": self.macro_allocation,
            "cuisine_mix": self.cuisine_mix,
            "recipe_source_summary": self.recipe_source_summary,
            "notes": self.notes,
        }


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
    "DietType",
    "GoalFit",
    "ProteinDensity",
    "CalorieDensity",
    "RecipeKind",
    "FoodItem",
    "MealFood",
    "NutritionPerServing",
    "Recipe",
    "Meal",
    "DayPlan",
    "MealPlan",
    "FitnessPlan",
]
