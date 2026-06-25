"""
Minimal food database — Phase-1 starter set of ~50 staple foods.

This is a FRAMEWORK-READY scaffold: the user will provide detailed food
resources later. The Phase-1 database covers the foundational proteins,
carbs, fats, vegetables, and fruits sufficient to generate 7-day meal
templates.

Future extension: load a richer database from JSON / external resource file.

All nutrition values are per 100 g unless noted. Sources: standard USDA
food composition data (same sources used by MacroFactor and FatCalc).
"""
from __future__ import annotations

from ..models.meal import FoodItem, FoodCategory


FOODS = [
    # === Animal proteins ===
    FoodItem("Chicken Breast (skinless, boneless, raw)", FoodCategory.PROTEIN_ANIMAL,
             120, 23.1, 0, 2.5, 0, 150, "1 medium breast (~150g)"),
    FoodItem("Chicken Thigh (skinless, raw)", FoodCategory.PROTEIN_ANIMAL,
             119, 19.3, 0, 4.3, 0, 150, "1 thigh (~150g)"),
    FoodItem("Lean Ground Beef (93/7, raw)", FoodCategory.PROTEIN_ANIMAL,
             164, 22.0, 0, 7.5, 0, 150, "1 serving (~150g)"),
    FoodItem("Fatty Ground Beef (80/20, raw)", FoodCategory.PROTEIN_ANIMAL,
             254, 17.2, 0, 20.0, 0, 150, "1 serving (~150g)"),
    FoodItem("Steak (Sirloin, raw)", FoodCategory.PROTEIN_ANIMAL,
             217, 26.0, 0, 12.5, 0, 200, "1 steak (~200g)"),
    FoodItem("Salmon (Atlantic, raw)", FoodCategory.PROTEIN_ANIMAL,
             208, 20.4, 0, 13.4, 0, 150, "1 fillet (~150g)"),
    FoodItem("Tuna (light, water-packed, drained)", FoodCategory.PROTEIN_ANIMAL,
             116, 25.5, 0, 0.8, 0, 120, "1 can (~120g)"),
    FoodItem("Cod (raw)", FoodCategory.PROTEIN_ANIMAL,
             82, 18.0, 0, 0.7, 0, 150, "1 fillet (~150g)"),
    FoodItem("Shrimp (raw)", FoodCategory.PROTEIN_ANIMAL,
             85, 20.3, 0, 0.5, 0, 120, "1 serving (~120g)"),
    FoodItem("Pork Loin (raw)", FoodCategory.PROTEIN_ANIMAL,
             143, 22.0, 0, 5.5, 0, 150, "1 chop (~150g)"),
    FoodItem("Turkey Breast (skinless, raw)", FoodCategory.PROTEIN_ANIMAL,
             117, 24.0, 0, 2.0, 0, 150, "1 serving (~150g)"),
    FoodItem("Whole Egg (large)", FoodCategory.PROTEIN_ANIMAL,
             155, 12.6, 1.1, 10.6, 0, 50, "1 egg (~50g)"),
    FoodItem("Egg White (large)", FoodCategory.PROTEIN_ANIMAL,
             52, 11.0, 0.7, 0.2, 0, 33, "1 white (~33g)"),
    FoodItem("Whey Protein Powder", FoodCategory.PROTEIN_ANIMAL,
             400, 80.0, 8.0, 6.0, 0, 30, "1 scoop (~30g)"),
    FoodItem("Greek Yogurt (non-fat, plain)", FoodCategory.DAIRY,
             59, 10.2, 3.6, 0.4, 0, 170, "1 cup (~170g)"),
    FoodItem("Cottage Cheese (low-fat, 2%)", FoodCategory.DAIRY,
             84, 11.0, 4.3, 1.2, 0, 226, "1 cup (~226g)"),
    FoodItem("Milk (skim)", FoodCategory.DAIRY,
             34, 3.4, 5.0, 0.1, 0, 240, "1 cup (~240mL)"),
    FoodItem("Cheddar Cheese", FoodCategory.DAIRY,
             403, 24.9, 1.3, 33.1, 0, 30, "1 slice (~30g)"),

    # === Plant proteins ===
    FoodItem("Tofu (firm)", FoodCategory.PROTEIN_PLANT,
             144, 17.3, 3.0, 8.7, 2.3, 150, "1 block (~150g)", is_vegan=True),
    FoodItem("Tempeh", FoodCategory.PROTEIN_PLANT,
             193, 20.3, 7.6, 10.8, 9.3, 100, "1 patty (~100g)", is_vegan=True),
    FoodItem("Lentils (cooked)", FoodCategory.PROTEIN_PLANT,
             116, 9.0, 20.0, 0.4, 7.9, 200, "1 cup (~200g)", is_vegan=True),
    FoodItem("Black Beans (cooked)", FoodCategory.PROTEIN_PLANT,
             132, 8.9, 23.7, 0.5, 8.7, 200, "1 cup (~200g)", is_vegan=True),
    FoodItem("Chickpeas (cooked)", FoodCategory.PROTEIN_PLANT,
             164, 8.9, 27.4, 2.6, 7.6, 200, "1 cup (~200g)", is_vegan=True),
    FoodItem("Edamame (cooked)", FoodCategory.PROTEIN_PLANT,
             121, 11.9, 9.0, 5.2, 5.2, 100, "1 cup (~100g)", is_vegan=True),
    FoodItem("Soy Protein Powder", FoodCategory.PROTEIN_PLANT,
             338, 80.0, 5.0, 1.5, 0, 30, "1 scoop (~30g)", is_vegan=True),
    FoodItem("Pea Protein Powder", FoodCategory.PROTEIN_PLANT,
             380, 80.0, 5.0, 7.0, 0, 30, "1 scoop (~30g)", is_vegan=True),
    FoodItem("Seitan (vital wheat gluten)", FoodCategory.PROTEIN_PLANT,
             370, 75.0, 14.0, 1.9, 0, 100, "1 serving (~100g)", is_vegan=True),

    # === Carb grains ===
    FoodItem("White Rice (cooked)", FoodCategory.CARB_GRAIN,
             130, 2.7, 28.2, 0.3, 0.4, 200, "1 cup (~200g)", is_vegan=True),
    FoodItem("Brown Rice (cooked)", FoodCategory.CARB_GRAIN,
             111, 2.6, 22.9, 0.9, 1.8, 200, "1 cup (~200g)", is_vegan=True),
    FoodItem("Oats (rolled, dry)", FoodCategory.CARB_GRAIN,
             389, 16.9, 66.3, 6.9, 10.6, 50, "1/2 cup (~50g)", is_vegan=True),
    FoodItem("Quinoa (cooked)", FoodCategory.CARB_GRAIN,
             120, 4.4, 21.3, 1.9, 2.8, 200, "1 cup (~200g)", is_vegan=True),
    FoodItem("Pasta (cooked)", FoodCategory.CARB_GRAIN,
             158, 5.8, 31.0, 0.9, 1.8, 200, "1 cup (~200g)", is_vegan=True),
    FoodItem("Whole Wheat Bread", FoodCategory.CARB_GRAIN,
             247, 13.0, 41.0, 4.2, 7.0, 30, "1 slice (~30g)", is_vegan=True),
    FoodItem("Tortilla (whole wheat)", FoodCategory.CARB_GRAIN,
             304, 8.0, 50.0, 7.0, 4.5, 45, "1 tortilla (~45g)", is_vegan=True),

    # === Carb starchy veg ===
    FoodItem("Sweet Potato (raw)", FoodCategory.CARB_STARCHY_VEG,
             86, 1.6, 20.1, 0.1, 3.0, 150, "1 medium (~150g)", is_vegan=True),
    FoodItem("Potato (white, raw)", FoodCategory.CARB_STARCHY_VEG,
             77, 2.0, 17.0, 0.1, 2.2, 150, "1 medium (~150g)", is_vegan=True),
    FoodItem("Corn (sweet, raw)", FoodCategory.CARB_STARCHY_VEG,
             86, 3.3, 19.0, 1.4, 2.7, 100, "1 ear (~100g)", is_vegan=True),

    # === Carb fruit ===
    FoodItem("Banana", FoodCategory.CARB_FRUIT,
             89, 1.1, 22.8, 0.3, 2.6, 120, "1 medium (~120g)", is_vegan=True),
    FoodItem("Apple", FoodCategory.CARB_FRUIT,
             52, 0.3, 13.8, 0.2, 2.4, 180, "1 medium (~180g)", is_vegan=True),
    FoodItem("Blueberries", FoodCategory.CARB_FRUIT,
             57, 0.7, 14.5, 0.3, 2.4, 100, "1 cup (~100g)", is_vegan=True),
    FoodItem("Strawberries", FoodCategory.CARB_FRUIT,
             32, 0.7, 7.7, 0.3, 2.0, 150, "1 cup (~150g)", is_vegan=True),
    FoodItem("Orange", FoodCategory.CARB_FRUIT,
             47, 0.9, 11.8, 0.1, 2.4, 130, "1 medium (~130g)", is_vegan=True),
    FoodItem("Pear", FoodCategory.CARB_FRUIT,
             57, 0.4, 15.2, 0.1, 3.1, 180, "1 medium (~180g)", is_vegan=True),

    # === Fat oil ===
    FoodItem("Olive Oil", FoodCategory.FAT_OIL,
             884, 0, 0, 100.0, 0, 14, "1 tbsp (~14mL)", is_vegan=True),
    FoodItem("Butter", FoodCategory.FAT_OIL,
             717, 0.9, 0.1, 81.1, 0, 14, "1 tbsp (~14g)"),
    FoodItem("Avocado (raw)", FoodCategory.FAT_OIL,
             160, 2.0, 8.5, 14.7, 6.7, 150, "1 medium (~150g)", is_vegan=True),

    # === Fat nut/seed ===
    FoodItem("Almonds (raw)", FoodCategory.FAT_NUT_SEED,
             579, 21.2, 21.6, 49.9, 12.5, 30, "1 oz (~30g)", is_vegan=True),
    FoodItem("Peanut Butter (natural)", FoodCategory.FAT_NUT_SEED,
             588, 25.1, 20.0, 50.4, 6.0, 32, "2 tbsp (~32g)", is_vegan=True),
    FoodItem("Walnuts (raw)", FoodCategory.FAT_NUT_SEED,
             654, 15.2, 13.7, 65.2, 6.7, 30, "1 oz (~30g)", is_vegan=True),
    FoodItem("Chia Seeds", FoodCategory.FAT_NUT_SEED,
             486, 16.5, 42.1, 30.7, 34.4, 28, "1 oz (~28g)", is_vegan=True),

    # === Vegetables ===
    FoodItem("Broccoli (raw)", FoodCategory.VEGETABLE,
             34, 2.8, 6.6, 0.4, 2.6, 90, "1 cup (~90g)", is_vegan=True),
    FoodItem("Spinach (raw)", FoodCategory.VEGETABLE,
             23, 2.9, 3.6, 0.4, 2.2, 30, "1 cup (~30g)", is_vegan=True),
    FoodItem("Mixed Salad Greens", FoodCategory.VEGETABLE,
             20, 1.5, 3.0, 0.2, 2.0, 60, "1 cup (~60g)", is_vegan=True),
    FoodItem("Bell Pepper (raw)", FoodCategory.VEGETABLE,
             31, 1.0, 6.0, 0.3, 2.1, 120, "1 medium (~120g)", is_vegan=True),
    FoodItem("Cucumber (raw)", FoodCategory.VEGETABLE,
             15, 0.7, 3.6, 0.1, 0.5, 100, "1/2 cup (~100g)", is_vegan=True),
    FoodItem("Carrots (raw)", FoodCategory.VEGETABLE,
             41, 0.9, 9.6, 0.2, 2.8, 60, "1/2 cup (~60g)", is_vegan=True),
    FoodItem("Asparagus (raw)", FoodCategory.VEGETABLE,
             20, 2.2, 3.9, 0.1, 2.1, 130, "5 spears (~130g)", is_vegan=True),
    FoodItem("Green Beans (raw)", FoodCategory.VEGETABLE,
             31, 1.8, 7.0, 0.1, 2.7, 100, "1 cup (~100g)", is_vegan=True),
    FoodItem("Onion (raw)", FoodCategory.VEGETABLE,
             40, 1.1, 9.3, 0.1, 1.7, 100, "1 medium (~100g)", is_vegan=True),
    FoodItem("Mushrooms (raw)", FoodCategory.VEGETABLE,
             22, 3.1, 3.3, 0.3, 1.0, 100, "1 cup (~100g)", is_vegan=True),

    # === Beverages ===
    FoodItem("Black Coffee", FoodCategory.BEVERAGE,
             1, 0.1, 0, 0, 0, 240, "1 cup (~240mL)", is_vegan=True),
    FoodItem("Green Tea", FoodCategory.BEVERAGE,
             1, 0, 0, 0, 0, 240, "1 cup (~240mL)", is_vegan=True),
]


# Index by name
FOOD_INDEX = {f.name: f for f in FOODS}


def get_food(name: str) -> FoodItem | None:
    """Look up a food by name."""
    return FOOD_INDEX.get(name)


def foods_by_category(category: FoodCategory) -> list[FoodItem]:
    """Return all foods in a given category."""
    return [f for f in FOODS if f.category == category]


def high_protein_foods(min_g_per_100g: float = 15.0) -> list[FoodItem]:
    """Return high-protein foods (≥15 g protein per 100 g)."""
    return [f for f in FOODS if f.protein_g_per_100g >= min_g_per_100g]


def protein_per_100kcal(food: FoodItem) -> float:
    """Protein per 100 kcal — useful for ranking protein density."""
    if food.kcal_per_100g <= 0:
        return 0
    return food.protein_g_per_100g / food.kcal_per_100g * 100


__all__ = [
    "FOODS", "FOOD_INDEX",
    "get_food", "foods_by_category", "high_protein_foods",
    "protein_per_100kcal",
]
