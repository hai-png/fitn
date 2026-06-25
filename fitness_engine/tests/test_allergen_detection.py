"""
Regression tests for Tier 1.4: word-boundary matching in
_recipe_has_meat_ingredients and check_allergens.

Previously the conditional-keyword loop only checked the character BEFORE
the keyword (so "eggplant" matched "egg" at pos=0 and skipped the boundary
check) and never checked the character AFTER. This caused vegan recipes
containing eggplant, butter lettuce, cream of tartar, etc. to be flagged
as containing meat and silently dropped from vegan queries.

The allergen check had the same substring-match flaw: "almond butter",
"coconut milk", "eggplant" all false-positive-matched dairy/egg allergens.
"""
import pytest

from fitness_engine.models.meal import Recipe, NutritionPerServing
from fitness_engine.meal_plan.recipe_loader import _recipe_has_meat_ingredients
from fitness_engine.meal_plan.recipe_scorer import check_allergens


def _make_recipe(ingredients: list[str], diet_types: list[str] = None) -> Recipe:
    return Recipe(
        name="Test Recipe",
        ingredients=ingredients,
        instructions=[],
        nutrition_per_serving=NutritionPerServing(),
        diet_types=diet_types or [],
    )


class TestRecipeHasMeatIngredients:
    """Tier 1.4 — _recipe_has_meat_ingredients must use word boundaries."""

    def test_eggplant_does_not_flag_as_meat(self):
        """eggplant contains 'egg' as substring but is a vegetable."""
        r = _make_recipe(["1 medium eggplant, diced", "2 tbsp olive oil", "salt"])
        assert _recipe_has_meat_ingredients(r) is False, (
            "eggplant must NOT be flagged as meat — this was the original bug"
        )

    def test_butter_lettuce_does_not_flag_as_meat(self):
        """butter lettuce contains 'butter' but is a vegetable."""
        r = _make_recipe(["1 head butter lettuce", "vinaigrette"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_cream_of_tartar_does_not_flag_as_meat(self):
        """cream of tartar contains 'cream' but is vegan."""
        r = _make_recipe(["1 tsp cream of tartar", "1 cup sugar"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_cocoa_butter_does_not_flag_as_meat(self):
        """cocoa butter is plant-based (cocoa)."""
        r = _make_recipe(["1/4 cup cocoa butter", "1/4 cup cocoa powder"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_almond_butter_does_not_flag_as_meat(self):
        """almond butter contains 'butter' but is plant-based."""
        r = _make_recipe(["2 tbsp almond butter", "1 banana"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_peanut_butter_does_not_flag_as_meat(self):
        """peanut butter contains 'butter' but is plant-based."""
        r = _make_recipe(["2 tbsp peanut butter", "1 slice bread"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_coconut_milk_does_not_flag_as_meat(self):
        """coconut milk contains 'milk' but is plant-based."""
        r = _make_recipe(["1 can coconut milk", "2 tbsp curry paste"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_real_egg_still_flags(self):
        """Genuine egg must still be flagged."""
        r = _make_recipe(["2 eggs", "1 tbsp butter", "salt"])
        assert _recipe_has_meat_ingredients(r) is True

    def test_real_butter_still_flags(self):
        """Genuine dairy butter must still be flagged."""
        r = _make_recipe(["1 cup flour", "1/2 cup butter", "1 cup sugar"])
        assert _recipe_has_meat_ingredients(r) is True

    def test_real_milk_still_flags(self):
        """Genuine dairy milk must still be flagged."""
        r = _make_recipe(["1 cup milk", "1/4 cup sugar", "vanilla"])
        assert _recipe_has_meat_ingredients(r) is True

    def test_real_chicken_still_flags(self):
        """Strict meat keyword 'chicken' must still flag."""
        r = _make_recipe(["1 lb chicken breast", "2 tbsp oil"])
        assert _recipe_has_meat_ingredients(r) is True

    def test_real_beef_still_flags(self):
        """Strict meat keyword 'beef' must still flag."""
        r = _make_recipe(["1 lb ground beef", "1 onion"])
        assert _recipe_has_meat_ingredients(r) is True

    def test_vegan_chicken_does_not_flag(self):
        """'vegan chicken' qualifier suppresses the strict 'chicken' match."""
        r = _make_recipe(["1 cup vegan chicken strips", "2 tbsp oil"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_no_chicken_broth_does_not_flag(self):
        """'no-chicken broth' (branded vegan product) must not flag.

        This was specifically called out in the audit — the hyphenated form
        'no-chicken' was missed because the qualifier list had 'no chicken'
        with a space.
        """
        r = _make_recipe(["2 cups no-chicken broth", "1 cup vegetables"])
        assert _recipe_has_meat_ingredients(r) is False

    def test_honey_flags_as_non_vegan(self):
        """Honey is an animal product — must flag for vegan queries."""
        r = _make_recipe(["1 tbsp honey", "1 cup oats", "1 cup water"])
        assert _recipe_has_meat_ingredients(r) is True


class TestCheckAllergens:
    """Tier 1.4 — check_allergens must use word boundaries + plant qualifiers."""

    def test_eggplant_does_not_violate_egg_allergy(self):
        """eggplant contains 'egg' substring but is safe for egg-allergic users."""
        r = _make_recipe(["1 medium eggplant", "olive oil", "salt"])
        violations = check_allergens(r, ["eggs"])
        assert violations == [], (
            f"eggplant must NOT trigger egg allergy; got {violations}"
        )

    def test_almond_butter_does_not_violate_dairy_allergy(self):
        """almond butter contains 'butter' substring but is dairy-free."""
        r = _make_recipe(["2 tbsp almond butter", "1 banana"])
        violations = check_allergens(r, ["dairy"])
        assert violations == []

    def test_coconut_milk_does_not_violate_dairy_allergy(self):
        """coconut milk contains 'milk' substring but is dairy-free."""
        r = _make_recipe(["1 can coconut milk", "curry paste"])
        violations = check_allergens(r, ["dairy"])
        assert violations == []

    def test_just_egg_does_not_violate_egg_allergy(self):
        """'Just Egg' is a branded plant-based egg substitute."""
        r = _make_recipe(["1/2 cup just egg", "1 tbsp oil", "salt"])
        violations = check_allergens(r, ["eggs"])
        assert violations == []

    def test_flax_egg_does_not_violate_egg_allergy(self):
        """'flax egg' is a plant-based egg substitute (flax + water)."""
        r = _make_recipe(["1 flax egg", "1 cup oats", "maple syrup"])
        violations = check_allergens(r, ["eggs"])
        assert violations == []

    def test_real_egg_still_violates_egg_allergy(self):
        r = _make_recipe(["2 eggs", "1 cup flour", "1 cup milk"])
        violations = check_allergens(r, ["eggs"])
        assert "eggs" in violations

    def test_real_milk_still_violates_dairy_allergy(self):
        r = _make_recipe(["1 cup milk", "1/4 cup sugar"])
        violations = check_allergens(r, ["dairy"])
        assert "dairy" in violations

    def test_real_butter_still_violates_dairy_allergy(self):
        r = _make_recipe(["1/2 cup butter", "1 cup sugar", "2 cups flour"])
        violations = check_allergens(r, ["dairy"])
        assert "dairy" in violations

    def test_real_cheese_still_violates_dairy_allergy(self):
        r = _make_recipe(["1 cup cheddar cheese", "1 tortilla"])
        violations = check_allergens(r, ["dairy"])
        assert "dairy" in violations

    def test_peanut_butter_violates_peanut_allergy(self):
        """peanut butter is safe for dairy, but must still trigger peanut allergy."""
        r = _make_recipe(["2 tbsp peanut butter", "1 slice bread"])
        # Dairy check — should NOT trigger (peanut butter is dairy-free)
        assert "dairy" not in check_allergens(r, ["dairy"])
        # Peanut check — SHOULD trigger
        assert "peanuts" in check_allergens(r, ["peanuts"])

    def test_fish_sauce_violates_fish_allergy(self):
        r = _make_recipe(["1 tbsp fish sauce", "1 clove garlic"])
        violations = check_allergens(r, ["fish"])
        assert "fish" in violations

    def test_multiple_allergens_in_one_recipe(self):
        r = _make_recipe(["1 cup milk", "2 eggs", "1 cup flour", "1 tbsp butter"])
        violations = check_allergens(r, ["dairy", "eggs", "gluten"])
        assert "dairy" in violations
        assert "eggs" in violations
        assert "gluten" in violations

    def test_no_allergens_returns_empty(self):
        r = _make_recipe(["1 cup rice", "1 cup beans", "1 tbsp oil"])
        violations = check_allergens(r, ["dairy", "eggs", "gluten", "soy", "nuts"])
        assert violations == []

    def test_empty_allergen_list_returns_empty(self):
        r = _make_recipe(["1 cup milk", "2 eggs"])
        assert check_allergens(r, []) == []

    def test_unknown_allergen_falls_back_to_word_boundary_match(self):
        """An allergen not in ALLERGEN_KEYWORDS should still match by name."""
        r = _make_recipe(["1 cup corn", "1 tbsp oil"])
        # 'corn' is not in the standard map; should still match by name
        violations = check_allergens(r, ["corn"])
        assert "corn" in violations
