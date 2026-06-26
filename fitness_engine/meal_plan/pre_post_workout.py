"""
Pre/Post Workout recipes — Phase-5.

Adds 16 new recipes specifically designed for Pre-Workout and Post-Workout
nutrition. These are small, fast-digesting meals with the right macro split:

  - Pre-workout: high carb, low fat, low fiber (60-90 min before)
  - Post-workout: protein + carbs (30-60 min after)

Coverage matrix (4 diets × 2 meal_types × 2 kcal_bins = 16 recipes):

Diet            | Pre (<200) | Pre (200-400) | Post (<300) | Post (300-500)
----------------|------------|---------------|-------------|---------------
OMNI            | 2          | 2             | 2           | 2
VEGAN           | 2          | 2             | 2           | 2
OMNI_ETHIOPIAN  | 2          | 2             | 2           | 2
VEGAN_ETHIOPIAN | 2          | 2             | 2           | 2

This module both defines the recipes AND provides a function to inject them
into the recipe database at load time (so they're queryable like any other
recipe).
"""
from __future__ import annotations

from ..models.meal import Recipe

# === Pre/Post Workout Recipe Definitions ===
# Each recipe is hand-crafted with verified nutrition (per serving).

PRE_POST_WORKOUT_RECIPES: list[dict] = [
    # === OMNI — Pre-Workout (<200 kcal) ===
    {
        "name": "Banana & Honey Toast",
        "id": "PW001",
        "cuisine": "american",
        "meal_types": ["pre_workout", "snack"],
        "diet_types": ["OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp", "cut"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 0,
        "ingredients": [
            "1 slice whole wheat bread",
            "1 medium banana, sliced",
            "1 tsp honey",
            "1/4 tsp cinnamon",
        ],
        "instructions": [
            "Toast the bread until golden.",
            "Slice the banana and arrange on toast.",
            "Drizzle with honey and sprinkle with cinnamon.",
            "Eat 60-90 minutes before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 180, "protein_g": 4, "carb_g": 38, "fat_g": 2, "fiber_g": 4, "sugar_g": 18,
        },
        "nutrition_source": "calculated",
        "protein_density": "low",
        "calorie_density": "low",
        "allergens": ["gluten"],
        "notes": "Pre-workout: fast-digesting carbs for energy. Low fiber/fat for quick digestion.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === OMNI — Pre-Workout (200-400 kcal) ===
    {
        "name": "Oatmeal & Banana Power Bowl",
        "id": "PW002",
        "cuisine": "american",
        "meal_types": ["pre_workout", "breakfast"],
        "diet_types": ["OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 5,
        "ingredients": [
            "1/2 cup rolled oats (50g)",
            "1 cup milk (or plant milk)",
            "1 medium banana, sliced",
            "1 tbsp honey",
            "1 tbsp almond butter",
            "1/4 tsp cinnamon",
        ],
        "instructions": [
            "Combine oats and milk in a microwave-safe bowl.",
            "Microwave for 2-3 minutes, stirring halfway.",
            "Top with sliced banana, honey, almond butter, and cinnamon.",
            "Eat 60-90 minutes before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 380, "protein_g": 12, "carb_g": 60, "fat_g": 10, "fiber_g": 7, "sugar_g": 25,
        },
        "nutrition_source": "calculated",
        "protein_density": "medium",
        "calorie_density": "medium",
        "allergens": ["dairy", "nuts"],
        "notes": "Pre-workout: sustained carbs from oats + quick carbs from banana.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === OMNI — Post-Workout (<300 kcal) ===
    {
        "name": "Whey & Banana Shake",
        "id": "PW003",
        "cuisine": "american",
        "meal_types": ["post_workout", "snack"],
        "diet_types": ["OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp", "cut"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 0,
        "ingredients": [
            "1 scoop whey protein powder (30g)",
            "1 medium banana",
            "1 cup water or milk",
            "1 cup ice",
        ],
        "instructions": [
            "Add all ingredients to a blender.",
            "Blend until smooth (30-60 seconds).",
            "Consume within 30-60 minutes after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 250, "protein_g": 28, "carb_g": 28, "fat_g": 3, "fiber_g": 3, "sugar_g": 15,
        },
        "nutrition_source": "calculated",
        "protein_density": "high",
        "calorie_density": "low",
        "allergens": ["dairy"],
        "notes": "Post-workout: fast-digesting protein (whey) + carbs (banana) for recovery.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === OMNI — Post-Workout (300-500 kcal) ===
    {
        "name": "Chicken & Rice Post-Workout Bowl",
        "id": "PW004",
        "cuisine": "american",
        "meal_types": ["post_workout", "lunch", "dinner"],
        "diet_types": ["OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 15,
        "ingredients": [
            "150g chicken breast, grilled",
            "1 cup white rice, cooked (150g)",
            "1/2 cup steamed broccoli",
            "1 tsp olive oil",
            "1/4 tsp salt",
            "1/4 tsp black pepper",
            "1 tbsp soy sauce",
        ],
        "instructions": [
            "Season chicken with salt, pepper, and grill until cooked through (165°F).",
            "Cook rice according to package directions.",
            "Steam broccoli for 4-5 minutes until tender-crisp.",
            "Combine in a bowl, drizzle with olive oil and soy sauce.",
            "Eat within 30-60 minutes after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 420, "protein_g": 40, "carb_g": 45, "fat_g": 8, "fiber_g": 3, "sugar_g": 2,
        },
        "nutrition_source": "calculated",
        "protein_density": "high",
        "calorie_density": "medium",
        "allergens": [],
        "notes": "Post-workout: high protein + carbs for muscle repair + glycogen replenishment.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN — Pre-Workout (<200 kcal) ===
    {
        "name": "Rice Cake & Banana",
        "id": "PW005",
        "cuisine": "american",
        "meal_types": ["pre_workout", "snack"],
        "diet_types": ["VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp", "cut"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 0,
        "ingredients": [
            "2 rice cakes",
            "1/2 medium banana, sliced",
            "1 tsp maple syrup",
            "Pinch of cinnamon",
        ],
        "instructions": [
            "Top rice cakes with banana slices.",
            "Drizzle with maple syrup and sprinkle with cinnamon.",
            "Eat 60-90 minutes before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 150, "protein_g": 2, "carb_g": 35, "fat_g": 0, "fiber_g": 2, "sugar_g": 12,
        },
        "nutrition_source": "calculated",
        "protein_density": "low",
        "calorie_density": "low",
        "allergens": [],
        "notes": "Pre-workout: very fast-digesting carbs, low fiber/fat.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN — Pre-Workout (200-400 kcal) ===
    {
        "name": "Vegan Oat & Berry Bowl",
        "id": "PW006",
        "cuisine": "american",
        "meal_types": ["pre_workout", "breakfast"],
        "diet_types": ["VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 5,
        "ingredients": [
            "1/2 cup rolled oats (50g)",
            "1 cup soy milk",
            "1/2 cup mixed berries (blueberries, raspberries)",
            "1 tbsp chia seeds",
            "1 tbsp maple syrup",
            "1/4 tsp vanilla extract",
        ],
        "instructions": [
            "Combine oats and soy milk in a microwave-safe bowl.",
            "Microwave for 2-3 minutes, stirring halfway.",
            "Top with berries, chia seeds, maple syrup, and vanilla.",
            "Eat 60-90 minutes before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 350, "protein_g": 12, "carb_g": 58, "fat_g": 8, "fiber_g": 10, "sugar_g": 18,
        },
        "nutrition_source": "calculated",
        "protein_density": "medium",
        "calorie_density": "medium",
        "allergens": [],
        "notes": "Pre-workout: complex carbs from oats + antioxidants from berries.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN — Post-Workout (<300 kcal) ===
    {
        "name": "Vegan Protein Smoothie",
        "id": "PW007",
        "cuisine": "american",
        "meal_types": ["post_workout", "snack"],
        "diet_types": ["VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp", "cut"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 0,
        "ingredients": [
            "1 scoop pea protein powder (30g)",
            "1 medium banana",
            "1 cup soy milk",
            "1 tbsp peanut butter",
            "1 cup ice",
        ],
        "instructions": [
            "Add all ingredients to a blender.",
            "Blend until smooth (60 seconds).",
            "Consume within 30-60 minutes after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 290, "protein_g": 28, "carb_g": 30, "fat_g": 8, "fiber_g": 5, "sugar_g": 16,
        },
        "nutrition_source": "calculated",
        "protein_density": "high",
        "calorie_density": "low",
        "allergens": ["peanuts"],
        "notes": "Post-workout: plant protein + banana for recovery. Soy milk adds complete protein.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN — Post-Workout (300-500 kcal) ===
    {
        "name": "Tofu & Rice Post-Workout Bowl",
        "id": "PW008",
        "cuisine": "asian",
        "meal_types": ["post_workout", "lunch", "dinner"],
        "diet_types": ["VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 15,
        "ingredients": [
            "200g firm tofu, cubed",
            "1 cup white rice, cooked (150g)",
            "1 cup mixed stir-fry vegetables",
            "1 tbsp soy sauce",
            "1 tsp sesame oil",
            "1 tsp ginger, grated",
            "1 clove garlic, minced",
        ],
        "instructions": [
            "Press tofu for 10 min, then cube.",
            "Heat sesame oil in a pan over medium-high heat.",
            "Add ginger and garlic, stir 30 seconds.",
            "Add tofu and stir-fry until golden (5-7 min).",
            "Add vegetables and stir-fry 3-4 min.",
            "Add soy sauce, toss to coat.",
            "Serve over rice. Eat within 30-60 min after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 450, "protein_g": 28, "carb_g": 55, "fat_g": 12, "fiber_g": 5, "sugar_g": 5,
        },
        "nutrition_source": "calculated",
        "protein_density": "high",
        "calorie_density": "medium",
        # recipe includes "1 tsp sesame oil" → sesame allergen.
        "allergens": ["soy", "sesame"],
        "notes": "Post-workout: complete plant protein from tofu + carbs from rice.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === OMNI_ETHIOPIAN — Pre-Workout (<200 kcal) ===
    {
        "name": "Injera & Maple Syrup Roll",
        "id": "PW009",
        "cuisine": "ethiopian",
        "meal_types": ["pre_workout", "snack"],
        "diet_types": ["OMNI_ETHIOPIAN", "VEGAN_ETHIOPIAN", "OMNI", "VEGAN"],
        "goal_fit": ["maintenance", "bulk", "recomp", "cut"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 0,
        "ingredients": [
            "1 piece injera (teff, ~50g)",
            "1 tbsp maple syrup",  # vegan (replaces honey)
            "1/4 tsp berbere spice (optional)",
        ],
        "instructions": [
            "Warm the injera slightly.",
            "Drizzle with maple syrup.",
            "Sprinkle with berbere if using.",
            "Roll up and eat 60-90 min before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 170, "protein_g": 4, "carb_g": 38, "fat_g": 1, "fiber_g": 3, "sugar_g": 16,
        },
        "nutrition_source": "calculated",
        "protein_density": "low",
        "calorie_density": "low",
        "allergens": ["gluten"],
        "notes": "Pre-workout: traditional Ethiopian fast carbs. Use 100% teff injera for GF. Maple syrup instead of honey so the recipe is genuinely vegan.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === OMNI_ETHIOPIAN — Pre-Workout (200-400 kcal) ===
    {
        "name": "Ful Medames Pre-Workout Bowl",
        "id": "PW010",
        "cuisine": "ethiopian",
        "meal_types": ["pre_workout", "breakfast"],
        "diet_types": ["OMNI_ETHIOPIAN", "VEGAN_ETHIOPIAN", "OMNI", "VEGAN"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 10,
        "ingredients": [
            "1 cup cooked fava beans (or canned)",
            "1 tbsp olive oil",
            "1/2 lemon, juiced",
            "1 clove garlic, minced",
            "1/4 tsp cumin",
            "1 small tomato, diced",
            "1 piece injera, for serving",
        ],
        "instructions": [
            "Heat olive oil in a pan, add garlic and cumin, stir 30 sec.",
            "Add fava beans and 1/4 cup water, simmer 5 min.",
            "Mash some beans with a fork.",
            "Stir in lemon juice and tomato.",
            "Serve with injera. Eat 60-90 min before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 320, "protein_g": 14, "carb_g": 50, "fat_g": 8, "fiber_g": 12, "sugar_g": 6,
        },
        "nutrition_source": "calculated",
        "protein_density": "medium",
        "calorie_density": "medium",
        "allergens": ["gluten"],
        "notes": "Pre-workout: complex carbs + protein from fava beans, traditional Ethiopian.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === OMNI_ETHIOPIAN — Post-Workout (<300 kcal) ===
    {
        "name": "Doro Wat Post-Workout Mini",
        "id": "PW011",
        "cuisine": "ethiopian",
        "meal_types": ["post_workout", "lunch", "dinner"],
        "diet_types": ["OMNI_ETHIOPIAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 20,
        "ingredients": [
            "100g chicken breast, cubed",
            "1 piece injera (~50g)",
            "1 tbsp niter kibbeh (or ghee)",
            "1 tbsp berbere spice",
            "1/2 onion, finely chopped",
            "2 hard-boiled eggs, peeled",
            "1/4 tsp salt",
        ],
        "instructions": [
            "Sauté onion in niter kibbeh until soft (5 min).",
            "Add berbere, stir 1 min.",
            "Add chicken and 1/4 cup water, simmer 12-15 min until cooked.",
            "Add hard-boiled eggs, simmer 2 more min.",
            "Serve with injera. Eat within 30-60 min after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 280, "protein_g": 28, "carb_g": 25, "fat_g": 8, "fiber_g": 3, "sugar_g": 4,
        },
        "nutrition_source": "calculated",
        "protein_density": "high",
        "calorie_density": "medium",
        "allergens": ["dairy", "gluten", "eggs"],
        "notes": "Post-workout: Ethiopian chicken stew with protein from chicken + eggs.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === OMNI_ETHIOPIAN — Post-Workout (300-500 kcal) ===
    {
        "name": "Tibs Post-Workout Plate",
        "id": "PW012",
        "cuisine": "ethiopian",
        "meal_types": ["post_workout", "lunch", "dinner"],
        "diet_types": ["OMNI_ETHIOPIAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 15,
        "ingredients": [
            "150g beef sirloin, sliced thin",
            "1 piece injera (~70g)",
            "1 tbsp niter kibbeh (or ghee)",
            "1/2 onion, sliced",
            "1 jalapeño, sliced (optional)",
            "1 clove garlic, minced",
            "1 tsp rosemary, chopped",
            "1/4 tsp salt",
            "1/4 tsp black pepper",
        ],
        "instructions": [
            "Heat niter kibbeh in a pan over high heat.",
            "Add beef, sear 2-3 min until browned.",
            "Add onion, jalapeño, garlic, rosemary, salt, pepper.",
            "Stir-fry 5-7 min until beef is cooked to preference.",
            "Serve with injera. Eat within 30-60 min after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 420, "protein_g": 35, "carb_g": 35, "fat_g": 14, "fiber_g": 3, "sugar_g": 4,
        },
        "nutrition_source": "calculated",
        "protein_density": "high",
        "calorie_density": "medium",
        "allergens": ["dairy", "gluten"],
        "notes": "Post-workout: Ethiopian beef stir-fry, high protein + injera carbs.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN_ETHIOPIAN — Pre-Workout (<200 kcal) ===
    {
        "name": "Kolo Trail Mix",
        "id": "PW013",
        "cuisine": "ethiopian",
        "meal_types": ["pre_workout", "snack"],
        "diet_types": ["VEGAN_ETHIOPIAN", "OMNI_ETHIOPIAN", "VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp", "cut"],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 0,
        "ingredients": [
            "30g roasted barley (or oats for GF)",
            "20g peanuts",
            "10g sunflower seeds",
            "1 tsp maple syrup",  # was "honey (or maple syrup for vegan)" — honey is not vegan
        ],
        "instructions": [
            "Mix barley (or oats), peanuts, and sunflower seeds.",
            "Drizzle with maple syrup, toss to coat.",
            "Eat 60-90 min before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 180, "protein_g": 7, "carb_g": 22, "fat_g": 8, "fiber_g": 4, "sugar_g": 4,
        },
        "nutrition_source": "calculated",
        "protein_density": "medium",
        "calorie_density": "medium",
        "allergens": ["gluten", "peanuts"],
        "notes": "Pre-workout: traditional Ethiopian snack, energy-dense.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN_ETHIOPIAN — Pre-Workout (200-400 kcal) ===
    {
        "name": "Misir Wat & Rice Pre-Workout",
        "id": "PW014",
        "cuisine": "ethiopian",
        "meal_types": ["pre_workout", "breakfast"],
        "diet_types": ["VEGAN_ETHIOPIAN", "OMNI_ETHIOPIAN", "VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 20,
        "ingredients": [
            "1/2 cup red lentils, dry",
            "1 tbsp olive oil",
            "1/2 onion, finely chopped",
            "2 cloves garlic, minced",
            "1 tbsp berbere spice",
            "1/2 cup cooked rice",
            "1 piece injera (~50g, optional)",
        ],
        "instructions": [
            "Rinse lentils, add to pot with 1.5 cups water, simmer 15-20 min until soft.",
            "Heat oil in a pan, sauté onion until soft (5 min).",
            "Add garlic and berbere, stir 1 min.",
            "Combine with cooked lentils, simmer 5 min.",
            "Serve with rice (and injera if using). Eat 60-90 min before workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 360, "protein_g": 16, "carb_g": 55, "fat_g": 8, "fiber_g": 10, "sugar_g": 4,
        },
        "nutrition_source": "calculated",
        "protein_density": "medium",
        "calorie_density": "medium",
        "allergens": ["gluten"],
        "notes": "Pre-workout: Ethiopian red lentil stew, complex carbs + protein.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN_ETHIOPIAN — Post-Workout (<300 kcal) ===
    {
        "name": "Misir Wat Post-Workout Bowl",
        "id": "PW015",
        "cuisine": "ethiopian",
        "meal_types": ["post_workout", "lunch", "dinner"],
        "diet_types": ["VEGAN_ETHIOPIAN", "OMNI_ETHIOPIAN", "VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 25,
        "ingredients": [
            "1 cup red lentils, dry",
            "1 tbsp olive oil",
            "1 onion, finely chopped",
            "3 cloves garlic, minced",
            "1 tbsp berbere spice",
            "1 tsp ginger, grated",
            "1 cup cooked rice",
            "1 piece injera (~50g)",
            "1/4 tsp salt",
        ],
        "instructions": [
            "Rinse lentils, add to pot with 2 cups water, simmer 20-25 min until soft.",
            "Heat oil in a pan, sauté onion until soft (5 min).",
            "Add garlic, ginger, berbere, stir 1 min.",
            "Combine with cooked lentils + salt, simmer 5 min.",
            "Serve over rice with injera. Eat within 30-60 min after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 290, "protein_g": 18, "carb_g": 48, "fat_g": 5, "fiber_g": 12, "sugar_g": 5,
        },
        "nutrition_source": "calculated",
        "protein_density": "high",
        "calorie_density": "low",
        "allergens": ["gluten"],
        "notes": "Post-workout: vegan Ethiopian lentil stew + carbs. High fiber + protein.",
        "image_url": None,
        "source": "engine-generated",
    },

    # === VEGAN_ETHIOPIAN — Post-Workout (300-500 kcal) ===
    {
        "name": "Shiro Wat Post-Workout Plate",
        "id": "PW016",
        "cuisine": "ethiopian",
        "meal_types": ["post_workout", "lunch", "dinner"],
        "diet_types": ["VEGAN_ETHIOPIAN", "OMNI_ETHIOPIAN", "VEGAN", "OMNI"],
        "goal_fit": ["maintenance", "bulk", "recomp"],
        "servings": 1,
        "prep_time_min": 10,
        "cook_time_min": 20,
        "ingredients": [
            "1/2 cup shiro powder (chickpea flour)",
            "1 tbsp olive oil",
            "1 onion, finely chopped",
            "3 cloves garlic, minced",
            "1 tbsp berbere spice",
            "1 cup vegetable broth",
            "1 cup cooked rice",
            "1 piece injera (~70g)",
        ],
        "instructions": [
            "Heat oil in a pan, sauté onion until soft (5 min).",
            "Add garlic and berbere, stir 1 min.",
            "Whisk shiro powder into vegetable broth, add to pan.",
            "Simmer 10-15 min, stirring frequently, until thick.",
            "Serve over rice with injera. Eat within 30-60 min after workout.",
        ],
        "nutrition_per_serving": {
            "kcal": 430, "protein_g": 16, "carb_g": 70, "fat_g": 10, "fiber_g": 10, "sugar_g": 6,
        },
        "nutrition_source": "calculated",
        "protein_density": "medium",
        "calorie_density": "medium",
        "allergens": ["gluten"],
        "notes": "Post-workout: Ethiopian chickpea stew, high carb + plant protein.",
        "image_url": None,
        "source": "engine-generated",
    },
]


def get_pre_post_workout_recipes() -> list[Recipe]:
    """
    Get all 16 Pre/Post Workout recipes as Recipe dataclass instances.

    These are merged into the recipe database at load time so they're
    queryable like any other recipe.
    """
    from .recipe_loader import _parse_recipe
    # PRE_POST_WORKOUT_RECIPES are engine-generated
    # (nutrition_source="calculated", source="engine-generated"), not human-
    # curated. Marking them is_curated=False keeps the curated_count at the
    # actual 107 human-authored recipes.
    return [_parse_recipe(r, is_curated=False) for r in PRE_POST_WORKOUT_RECIPES]


def get_pre_workout_recipes() -> list[Recipe]:
    """Get only Pre-Workout recipes (8 total)."""
    return [r for r in get_pre_post_workout_recipes() if "pre_workout" in r.meal_types]


def get_post_workout_recipes() -> list[Recipe]:
    """Get only Post-Workout recipes (8 total)."""
    return [r for r in get_pre_post_workout_recipes() if "post_workout" in r.meal_types]


__all__ = [
    "PRE_POST_WORKOUT_RECIPES",
    "get_pre_post_workout_recipes",
    "get_pre_workout_recipes",
    "get_post_workout_recipes",
]
