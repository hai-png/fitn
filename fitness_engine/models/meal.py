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

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

# shared JSON-serializer for consistent Enum conversion.
from ..utils.serialize import convert_for_json


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


class RecipeDietTag(str, Enum):
    """Recipe diet_type tags (uppercase, matches recipe database JSON).

    Phase-6 fix: renamed from `DietType` to avoid collision with
    `fitness_engine.models.profile.DietType` (lowercase user-facing values).
    The two enums serve different purposes:
      - profile.DietType  → user's selected diet (omnivore, vegan, keto, ...)
      - meal.RecipeDietTag → recipe database tag (OMNI, VEGAN, OMNI_ETHIOPIAN, ...)
    """
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


# === Raw food model (kept for backward compat) ===

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
        return self.food.fiber_g_per_100g * self.grams / 100


# === Recipe model ===

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
    id: str | None = None               # e.g. "R001"
    source: str | None = None            # URL
    source_file: str | None = None
    # === Classification ===
    cuisine: str = "american"
    category: str = ""                      # free-text: "dinner, main, main course"
    recipe_kind: str = "meal"               # "meal" or "pantry"
    meal_types: list[str] = field(default_factory=list)   # ["breakfast", "lunch", ...]
    diet_types: list[str] = field(default_factory=list)   # ["OMNI", "VEGAN", ...]
    goal_fit: list[str] = field(default_factory=list)     # ["maintenance", "cut", ...]

    # === Servings & timing ===
    servings: int = 1
    prep_time_min: int | None = None
    cook_time_min: int | None = None

    # === Content ===
    ingredients: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)

    # === Nutrition (per serving) ===
    nutrition_per_serving: NutritionPerServing = field(default_factory=NutritionPerServing)
    nutrition_source: str = "published"    # "published" or "estimated"
    serving_size_g: float | None = None

    # === Quality / density tags ===
    protein_density: str | None = None  # "low" / "medium" / "high"
    calorie_density: str | None = None  # "low" / "medium" / "high"
    allergens: list[str] = field(default_factory=list)
    alternative_recipe_ids: list[str] = field(default_factory=list)

    # === Cultural flags (Ethiopian cuisine specific) ===
    fasting_yetsom: bool = False            # Ethiopian Orthodox fasting-friendly
    injera_accompaniment: bool = False      # served with injera

    # === Media ===
    image_url: str | None = None

    # v3.1.5 Task 3: selection reason + top alternatives (computed by the
    # curate script and attached to each recipe). These surface in the meal
    # plan output so users understand WHY a recipe was chosen and what else
    # they could swap to.
    selection_reason: str = ""              # e.g. "High-protein breakfast for muscle_gain"
    top_alternatives: list[dict] = field(default_factory=list)
    # Each alternative dict: {"id": "R042", "name": "...", "kcal": 320, "protein_g": 28, "cuisine": "ethiopian", "similarity": 0.85}

    # === Misc ===
    notes: str = ""
    @property
    def total_time_min(self) -> int | None:
        """Total prep + cook time, or None if either is missing."""
        if self.prep_time_min is None or self.cook_time_min is None:
            return None
        return self.prep_time_min + self.cook_time_min

    @property
    def is_vegan(self) -> bool:
        """True if the recipe is vegan (including VEGAN_ETHIOPIAN etc.).

        Phase-6 fix: previously used exact equality `d.upper() == "VEGAN"`,
        which missed `VEGAN_ETHIOPIAN` and other `VEGAN_*` tags. Now matches
        any tag that equals "VEGAN" or starts with "VEGAN_", consistent with
        `recipes_by_filters` and `score_diet_match`.
        """
        for d in self.diet_types:
            du = d.upper()
            if du == "VEGAN" or du.startswith("VEGAN_"):
                return True
        return False

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
        # use convert_for_json for consistent Enum conversion (also
        # consistent with Meal.to_dict which explicitly converts Enums).
        return convert_for_json(self)


# === Meal / Day / Plan ===

@dataclass
class Meal:
    """
    A single meal.

    Phase-2 supports two modes:
      1. Recipe-based: `recipe` is set; `foods` holds fillers. The meal is a
         single cohesive dish (e.g. "Chechebsa") with full ingredients +
         instructions, optionally scaled via `scale_factor` and supplemented
         with fillers in `foods`.
      2. Raw-foods-based (Phase-1 fallback): `recipe` is None; `foods` is
         populated with MealFood entries.

    Both modes carry target macros (the planner's per-meal allocation)
    and the actual macros of whatever was selected.

    Tier 1.2 fix: `scale_factor`, `scaled_kcal/protein_g/carb_g/fat_g/fiber_g`,
    `swap_options`, and `ingredient_swaps` fields are now first-class. The
    `total_*` properties use scaled nutrition + filler contributions when a
    recipe is present (previously they returned the *unscaled* `recipe.kcal`
    and ignored fillers entirely, producing JSON output that contradicted the
    planner's own weekly summary).
    """
    meal_type: MealType
    name: str
    foods: list[MealFood] = field(default_factory=list)
    recipe: Recipe | None = None
    # Scaled recipe nutrition. When `recipe` is set, these hold the
    # scaled per-serving values; `total_*` properties add filler contributions
    # on top. When `recipe` is None, they're 0 and `total_*` falls back to
    # summing `foods` only.
    scale_factor: float = 1.0
    scaled_kcal: float = 0.0
    scaled_protein_g: float = 0.0
    scaled_carb_g: float = 0.0
    scaled_fat_g: float = 0.0
    scaled_fiber_g: float = 0.0
    # Swap options + targets preserved end-to-end (allocator → planner → JSON).
    swap_options: list[dict] = field(default_factory=list)
    ingredient_swaps: dict = field(default_factory=dict)
    target_kcal: float = 0.0
    target_protein_g: float = 0.0
    target_carb_g: float = 0.0
    target_fat_g: float = 0.0
    # v3.1.5 LOW-14: target_fiber_g was missing — fiber targets were dropped
    # during slot→meal conversion. Now preserved end-to-end so the JSON output
    # and weekly summary can report fiber match percentages.
    target_fiber_g: float = 0.0
    notes: str = ""

    @property
    def total_kcal(self) -> float:
        if self.recipe is not None:
            # Scaled recipe + fillers.
            return self.scaled_kcal + sum(f.kcal for f in self.foods)
        return sum(f.kcal for f in self.foods)

    @property
    def total_protein_g(self) -> float:
        if self.recipe is not None:
            return self.scaled_protein_g + sum(f.protein_g for f in self.foods)
        return sum(f.protein_g for f in self.foods)

    @property
    def total_carb_g(self) -> float:
        if self.recipe is not None:
            return self.scaled_carb_g + sum(f.carb_g for f in self.foods)
        return sum(f.carb_g for f in self.foods)

    @property
    def total_fat_g(self) -> float:
        if self.recipe is not None:
            return self.scaled_fat_g + sum(f.fat_g for f in self.foods)
        return sum(f.fat_g for f in self.foods)

    @property
    def total_fiber_g(self) -> float:
        if self.recipe is not None:
            return self.scaled_fiber_g + sum(f.fiber_g for f in self.foods)
        return sum(f.fiber_g for f in self.foods)

    def to_dict(self) -> dict:
        return {
            "meal_type": self.meal_type.value if isinstance(self.meal_type, MealType) else self.meal_type,
            "name": self.name,
            "recipe": self.recipe.to_dict() if self.recipe else None,
            "scale_factor": self.scale_factor,
            "scaled_nutrition": {
                "kcal": round(self.scaled_kcal, 1),
                "protein_g": round(self.scaled_protein_g, 1),
                "carb_g": round(self.scaled_carb_g, 1),
                "fat_g": round(self.scaled_fat_g, 1),
                "fiber_g": round(self.scaled_fiber_g, 1),
            },
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
                    "kcal": round(f.kcal, 1),
                    "protein_g": round(f.protein_g, 1),
                    "carb_g": round(f.carb_g, 1),
                    "fat_g": round(f.fat_g, 1),
                    # include fiber_g per food.
                    "fiber_g": round(f.fiber_g, 1),
                }
                for f in self.foods
            ],
            "swap_options": self.swap_options,
            "ingredient_swaps": self.ingredient_swaps,
            "target_kcal": self.target_kcal,
            "target_protein_g": self.target_protein_g,
            "target_carb_g": self.target_carb_g,
            "target_fat_g": self.target_fat_g,
            "actual_kcal": round(self.total_kcal, 1),
            "actual_protein_g": round(self.total_protein_g, 1),
            "actual_carb_g": round(self.total_carb_g, 1),
            "actual_fat_g": round(self.total_fat_g, 1),
            # include actual_fiber_g.
            "actual_fiber_g": round(self.total_fiber_g, 1),
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

    @property
    def total_fiber_g(self) -> float:
        return sum(m.total_fiber_g for m in self.meals)

    def to_dict(self) -> dict:
        return {
            "day_number": self.day_number,
            "day_name": self.day_name,
            "meals": [m.to_dict() for m in self.meals],
            "total_kcal": self.total_kcal,
            "total_protein_g": self.total_protein_g,
            "total_carb_g": self.total_carb_g,
            "total_fat_g": self.total_fat_g,
            # include total_fiber_g.
            "total_fiber_g": round(self.total_fiber_g, 1),
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

    def __post_init__(self):
        # validate that all three sub-plans are non-None. A None
        # value here would silently produce a AttributeError downstream when
        # to_dict() tries to call .to_dict() on the sub-plan.
        missing = [
            name for name, val in (
                ("nutrition", self.nutrition),
                ("training", self.training),
                ("meal", self.meal),
            ) if val is None
        ]
        if missing:
            raise ValueError(
                f"FitnessPlan requires non-None sub-plans; missing: {missing}"
            )

    def to_dict(self) -> dict:
        return {
            "nutrition": self.nutrition.to_dict(),
            "training": self.training.to_dict(),
            "meal": self.meal.to_dict(),
            "summary": self.summary,
        }


# TYPE_CHECKING + deferred imports inside to_dict() to avoid circular
# import at module load time.
if TYPE_CHECKING:
    from .nutrition import NutritionPlan
    from .training import TrainingPlan


__all__ = [
    "MealType",
    "FoodCategory",
    "RecipeDietTag",
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
