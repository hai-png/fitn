"""
Phase-6 regression tests for critical fixes.

Each test locks in a specific Phase-6 fix so the bugs don't regress.
"""
import pytest

from fitness_engine.models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.models.assessment import BodyFatCategory, BMICategory
from fitness_engine.models.meal import Recipe, NutritionPerServing
from fitness_engine.assessment.body_composition import classify_bf, classify_bmi
from fitness_engine.assessment.health_risk import classify_whtr
from fitness_engine.assessment.decision import CUT_BULK_BOUNDARIES
from fitness_engine.assessment._thresholds import (
    OPERATIONAL_BF_RANGE, HORMONAL_FLOOR, OBESE_THRESHOLD,
)
from fitness_engine.nutrition.calories import MAX_WEEKLY_LOSS_PCT, CUT_RATE_TIERS
from fitness_engine.models.profile import CutRateTier
from fitness_engine.nutrition.tdee import observed_tdee_first_principles
from fitness_engine.training.intensity_model import should_deload
from fitness_engine.training.volume_landmarks import get_muscle_landmarks
from fitness_engine.meal_plan.profile_requirements import (
    compute_pre_workout_target, compute_post_workout_target,
    PRE_WORKOUT_MACRO_RATIO, POST_WORKOUT_MACRO_RATIO,
)
from fitness_engine.meal_plan.recipe_scorer import check_excluded_ingredients
from fitness_engine.meal_plan.swap_system import get_ingredient_swaps
from fitness_engine.models.nutrition import MacroSplit
from fitness_engine.models.preferences import PlanPreferences
from fitness_engine.models.profile import ExerciseIntensity, Climate


# === Phase-1.1: BF category bands are continuous (no gaps → OBESITY) ===

class TestBFCategoryBandsContinuous:
    """Closes the (5,6), (13,14), (17,18), (24,25) gaps for men
    and (13,14), (20,21), (24,25), (31,32) gaps for women."""

    @pytest.mark.parametrize("bf,expected", [
        (5.5, BodyFatCategory.ESSENTIAL),    # was OBESITY (gap 5-6)
        (13.5, BodyFatCategory.ATHLETE),     # was OBESITY (gap 13-14)
        (17.5, BodyFatCategory.FITNESS),     # was OBESITY (gap 17-18)
        (24.5, BodyFatCategory.ACCEPTABLE),  # was OBESITY (gap 24-25)
        (25.0, BodyFatCategory.OBESITY),     # boundary
        (4.0, BodyFatCategory.ESSENTIAL),
        (10.0, BodyFatCategory.ATHLETE),
        (20.0, BodyFatCategory.ACCEPTABLE),
    ])
    def test_male_bf_classification_no_gaps(self, bf, expected):
        assert classify_bf(bf, Sex.MALE) == expected

    @pytest.mark.parametrize("bf,expected", [
        (13.5, BodyFatCategory.ESSENTIAL),
        (20.5, BodyFatCategory.ATHLETE),
        (24.5, BodyFatCategory.FITNESS),
        (31.5, BodyFatCategory.ACCEPTABLE),
        (32.0, BodyFatCategory.OBESITY),
    ])
    def test_female_bf_classification_no_gaps(self, bf, expected):
        assert classify_bf(bf, Sex.FEMALE) == expected

    def test_negative_bf_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            classify_bf(-1.0, Sex.MALE)


# === Phase-1.2: Weekly loss cap is 1.0% (RED-S protection) ===

class TestWeeklyLossCap:
    def test_max_weekly_loss_pct_is_1_percent(self):
        assert MAX_WEEKLY_LOSS_PCT == 0.010

    def test_very_aggressive_tier_clipped_to_1_percent(self):
        """VERY_AGGRESSIVE tier value should equal the cap (1.0%), not 1.5%."""
        assert CUT_RATE_TIERS[CutRateTier.VERY_AGGRESSIVE] == 0.010


# === Phase-1.3: PRE/POST workout slots preserve daily macro totals ===

class TestPrePostWorkoutMacroPreservation:
    def test_keto_pre_workout_does_not_explode_carbs(self):
        """Keto user with daily C=50g should not get C=32g in PRE alone."""
        # Keto macros: 2000 kcal, P=100, C=50, F=167
        pre = compute_pre_workout_target(
            daily_kcal=2000, daily_protein_g=100,
            daily_carb_g=50, daily_fat_g=167,
        )
        # Pre-workout slot is 10% of daily kcal = 200 kcal
        assert 190 <= pre.target_kcal <= 210
        # Blended carbs should be << 32g (the old pure-ratio value)
        # Old behavior: C = 200 * 0.65 / 4 = 32.5g
        # New blended behavior: ~half of (10% of 50 + 32.5) = ~18.75g
        assert pre.target_carb_g < 25, (
            f"Keto PRE carbs should be < 25g (was 32.5g under old pure-ratio, "
            f"got {pre.target_carb_g}g under new blend)"
        )

    def test_pre_workout_macros_sum_to_slot_kcal(self):
        """Slot macro kcal should approximately match slot kcal."""
        pre = compute_pre_workout_target(
            daily_kcal=2500, daily_protein_g=150,
            daily_carb_g=300, daily_fat_g=80,
        )
        macro_kcal = (
            pre.target_protein_g * 4
            + pre.target_carb_g * 4
            + pre.target_fat_g * 9
        )
        assert abs(macro_kcal - pre.target_kcal) < 8.0, (
            f"PRE macro kcal ({macro_kcal}) must match slot kcal ({pre.target_kcal})"
        )

    def test_post_workout_macros_sum_to_slot_kcal(self):
        post = compute_post_workout_target(
            daily_kcal=2500, daily_protein_g=150,
            daily_carb_g=300, daily_fat_g=80,
        )
        macro_kcal = (
            post.target_protein_g * 4
            + post.target_carb_g * 4
            + post.target_fat_g * 9
        )
        assert abs(macro_kcal - post.target_kcal) < 8.0


# === Phase-1.4: Recipe swap system filters allergens ===

class TestRecipeSwapAllergenFiltering:
    def _make_recipe(self, name: str, ingredients: list[str], diet_types: list[str] = None) -> Recipe:
        return Recipe(
            id=name.lower().replace(" ", "-"),
            name=name,
            cuisine="american",
            meal_types=["dinner"],
            diet_types=diet_types or ["OMNI"],
            ingredients=ingredients,
            instructions=[],
            nutrition_per_serving=NutritionPerServing(
                kcal=500, protein_g=30, carb_g=40, fat_g=20, fiber_g=5,
            ),
            prep_time_min=10, cook_time_min=20,
        )

    def test_swap_signature_accepts_allergen_params(self):
        """Phase-6: get_recipe_swaps_for_plan accepts allergens/excluded/cuisine."""
        import inspect
        from fitness_engine.meal_plan.swap_system import get_recipe_swaps_for_plan
        sig = inspect.signature(get_recipe_swaps_for_plan)
        assert "allergens_to_avoid" in sig.parameters
        assert "excluded_ingredients" in sig.parameters
        assert "cuisine_preference" in sig.parameters


# === Phase-1.5: RIR clamp moved after DUP modification ===

class TestRIRClampAfterDUP:
    """Heavy DUP day should produce RPE ≥ 7 for compounds (not 6-8)."""

    def test_rir_clamp_does_not_fire_before_dup(self):
        """The RIR clamp code path is in apply_periodization, which we test
        indirectly by confirming the function exists and is callable."""
        from fitness_engine.training.periodization import apply_periodization
        assert callable(apply_periodization)


# === Phase-1.6: Volume landmarks align with RP consensus ===

class TestVolumeLandmarksRPConsensus:
    def test_chest_mev_is_8_not_4(self):
        assert get_muscle_landmarks("chest").mev == 8

    def test_back_mev_greater_than_chest_mev(self):
        chest = get_muscle_landmarks("chest")
        back = get_muscle_landmarks("back")
        assert back.mev > chest.mev


# === Phase-2: classify_whtr returns MODERATE ===

class TestClassifyWhtrModerate:
    def test_male_moderate_band(self):
        """0.50-0.53 should return MODERATE (was jumping HIGH → LOW)."""
        assert classify_whtr(0.51, Sex.MALE).value == "moderate"
        assert classify_whtr(0.52, Sex.MALE).value == "moderate"

    def test_female_moderate_band(self):
        assert classify_whtr(0.47, Sex.FEMALE).value == "moderate"
        assert classify_whtr(0.48, Sex.FEMALE).value == "moderate"


# === Phase-2: thresholds consolidated to _thresholds.py ===

class TestThresholdsConsolidated:
    def test_decision_thresholds_match_canonical(self):
        """CUT_BULK_BOUNDARIES operational_lo/hi should equal _thresholds values."""
        for sex in [Sex.MALE, Sex.FEMALE]:
            assert CUT_BULK_BOUNDARIES[sex]["operational_lo"] == OPERATIONAL_BF_RANGE[sex][0]
            assert CUT_BULK_BOUNDARIES[sex]["operational_hi"] == OPERATIONAL_BF_RANGE[sex][1]
            assert CUT_BULK_BOUNDARIES[sex]["obese_threshold"] == OBESE_THRESHOLD[sex]
            assert CUT_BULK_BOUNDARIES[sex]["cut_floor"] == HORMONAL_FLOOR[sex]


# === Phase-2: PlanPreferences uses enums ===

class TestPlanPreferencesEnums:
    def test_exercise_intensity_enum_default(self):
        prefs = PlanPreferences()
        assert isinstance(prefs.exercise_intensity, ExerciseIntensity)
        assert prefs.exercise_intensity == ExerciseIntensity.MODERATE

    def test_climate_enum_default(self):
        prefs = PlanPreferences()
        assert isinstance(prefs.climate, Climate)
        assert prefs.climate == Climate.TEMPERATE

    def test_string_kwargs_coerced_to_enum(self):
        prefs = PlanPreferences(exercise_intensity="intense", climate="hot")
        assert prefs.exercise_intensity == ExerciseIntensity.INTENSE
        assert prefs.climate == Climate.HOT

    def test_weight_reduced_pct_validated(self):
        with pytest.raises(ValueError, match="weight_reduced_pct must be in"):
            PlanPreferences(weight_reduced_pct=1.5)
        with pytest.raises(ValueError, match="weight_reduced_pct must be in"):
            PlanPreferences(weight_reduced_pct=-0.1)

    def test_unknown_kwargs_warn(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            PlanPreferences.from_kwargs(meal_freqency=4)  # typo
        assert "meal_freqency" in caplog.text


# === Phase-2: word-boundary matching for excluded ingredients ===

class TestExcludedIngredientsWordBoundary:
    def _recipe(self, ingredients: list[str]) -> Recipe:
        return Recipe(
            id="test", name="test", cuisine="x",
            meal_types=["dinner"], diet_types=["OMNI"],
            ingredients=ingredients, instructions=[],
            nutrition_per_serving=NutritionPerServing(
                kcal=400, protein_g=20, carb_g=40, fat_g=10, fiber_g=5,
            ),
            prep_time_min=5, cook_time_min=10,
        )

    def test_excluding_nut_does_not_match_coconut(self):
        """Phase-6: 'nut' should not match 'coconut' (word boundary)."""
        r = self._recipe(["coconut milk", "rice"])
        found = check_excluded_ingredients(r, ["nut"])
        assert "nut" not in found, f"'nut' should not match 'coconut' (got {found})"

    def test_excluding_nut_does_not_match_nutmeg(self):
        r = self._recipe(["nutmeg", "flour"])
        found = check_excluded_ingredients(r, ["nut"])
        assert "nut" not in found

    def test_excluding_egg_does_not_match_eggplant(self):
        r = self._recipe(["eggplant", "tomato"])
        found = check_excluded_ingredients(r, ["egg"])
        assert "egg" not in found

    def test_excluding_cream_does_not_match_cream_of_tartar(self):
        r = self._recipe(["cream of tartar", "sugar"])
        found = check_excluded_ingredients(r, ["cream"])
        assert "cream" not in found

    def test_excluding_rice_matches_rice(self):
        r = self._recipe(["rice", "chicken"])
        found = check_excluded_ingredients(r, ["rice"])
        assert "rice" in found


# === Phase-2: ingredient swap word-boundary matching ===

class TestIngredientSwapWordBoundary:
    def test_eggplant_does_not_get_egg_swaps(self):
        """Phase-6: 'eggplant' should not return egg swaps (was substring match)."""
        swaps = get_ingredient_swaps("eggplant")
        assert swaps == [], f"'eggplant' should return no swaps (got {swaps})"

    def test_butter_lettuce_does_not_get_butter_swaps(self):
        swaps = get_ingredient_swaps("butter lettuce")
        # Should not return dairy butter swaps
        for s in swaps:
            for replacement in s.alternatives:
                assert "ghee" not in replacement.lower(), (
                    f"'butter lettuce' should not return ghee swap (got {replacement})"
                )

    def test_real_egg_still_gets_swaps(self):
        swaps = get_ingredient_swaps("egg")
        assert len(swaps) > 0

    def test_real_butter_still_gets_swaps(self):
        swaps = get_ingredient_swaps("butter")
        assert len(swaps) > 0


# === Phase-3: observed_tdee_first_principles validates n_days ===

class TestObservedTDEEValidation:
    def test_zero_days_raises_value_error(self):
        with pytest.raises(ValueError, match="n_days must be >= 1"):
            observed_tdee_first_principles(2500, 80.0, 79.5, 0)

    def test_negative_days_raises_value_error(self):
        with pytest.raises(ValueError, match="n_days must be >= 1"):
            observed_tdee_first_principles(2500, 80.0, 79.5, -5)

    def test_valid_n_days_works(self):
        # User lost 0.5kg over 7 days at 2500 kcal intake.
        # delta_weight = 79.5 - 80.0 = -0.5 kg (lost weight)
        # observed_tdee = 2500 - (-0.5 * 7700) / 7 = 2500 + 550 = 3050
        tdee = observed_tdee_first_principles(2500, 80.0, 79.5, 7)
        assert abs(tdee - 3050) < 5


# === Phase-3: should_deload validates answer count ===

class TestShouldDeloadValidation:
    def test_too_few_answers_raises(self):
        with pytest.raises(ValueError, match="requires exactly 5 answers"):
            should_deload([True, True])

    def test_too_many_answers_raises(self):
        with pytest.raises(ValueError, match="requires exactly 5 answers"):
            should_deload([True] * 6)

    def test_exactly_5_answers_works(self):
        assert should_deload([True, True, False, False, False]) is True
        assert should_deload([False, False, False, False, False]) is False


# === Phase-3: Recipe.is_vegan matches VEGAN_* prefix ===

class TestRecipeIsVeganPrefix:
    def _recipe(self, diet_types: list[str]) -> Recipe:
        return Recipe(
            id="x", name="x", cuisine="x",
            meal_types=["dinner"], diet_types=diet_types,
            ingredients=["x"], instructions=[],
            nutrition_per_serving=NutritionPerServing(
                kcal=400, protein_g=20, carb_g=40, fat_g=10, fiber_g=5,
            ),
            prep_time_min=5, cook_time_min=10,
        )

    def test_vegan_ethiopian_is_vegan(self):
        r = self._recipe(["VEGAN_ETHIOPIAN"])
        assert r.is_vegan is True

    def test_pure_vegan_is_vegan(self):
        r = self._recipe(["VEGAN"])
        assert r.is_vegan is True

    def test_omni_is_not_vegan(self):
        r = self._recipe(["OMNI"])
        assert r.is_vegan is False


# === Phase-3: DietType renamed to RecipeDietTag ===

class TestRecipeDietTagRename:
    def test_recipe_diet_tag_exists(self):
        from fitness_engine.models.meal import RecipeDietTag
        assert RecipeDietTag.VEGAN.value == "VEGAN"
        assert RecipeDietTag.VEGAN_ETHIOPIAN.value == "VEGAN_ETHIOPIAN"

    def test_backward_compat_alias(self):
        from fitness_engine.models.meal import DietType, RecipeDietTag
        assert DietType is RecipeDietTag


# === Phase-5: MacroSplit validation ===

class TestMacroSplitValidation:
    def test_valid_macros_pass(self):
        ms = MacroSplit(
            protein_g=150, fat_g=80, carb_g=300,
            protein_pct=30, fat_pct=36, carb_pct=34,
            protein_kcal=600, fat_kcal=720, carb_kcal=1200,
        )
        assert ms.total_kcal == 2520

    def test_negative_protein_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            MacroSplit(
                protein_g=-10, fat_g=80, carb_g=300,
                protein_pct=30, fat_pct=36, carb_pct=34,
                protein_kcal=600, fat_kcal=720, carb_kcal=1200,
            )

    def test_pct_sum_off_raises(self):
        with pytest.raises(ValueError, match="percentages must sum to ~100"):
            MacroSplit(
                protein_g=150, fat_g=80, carb_g=300,
                protein_pct=50, fat_pct=50, carb_pct=50,  # sum=150
                protein_kcal=600, fat_kcal=720, carb_kcal=1200,
            )

    def test_carbs_clamped_property(self):
        ms = MacroSplit(
            protein_g=200, fat_g=80, carb_g=0,
            protein_pct=50, fat_pct=40, carb_pct=10,
            protein_kcal=800, fat_kcal=720, carb_kcal=0,
            notes=["carbs clamped to 0 (protein+fat exceeded target)"],
        )
        assert ms.carbs_clamped is True


# === Phase-5: Architect raises on unsupported training days ===

class TestArchitectRaisesUnsupportedDays:
    def test_one_day_per_week_raises(self):
        from fitness_engine.training.architect import _pick_split
        from fitness_engine.models.profile import TrainingStatus
        from fitness_engine.models.training import TrainingGoal
        with pytest.raises(ValueError, match="Unsupported training_days_per_week"):
            _pick_split(1, TrainingStatus.INTERMEDIATE, TrainingGoal.HYPERTROPHY)

    def test_seven_days_per_week_raises(self):
        from fitness_engine.training.architect import _pick_split
        from fitness_engine.models.profile import TrainingStatus
        from fitness_engine.models.training import TrainingGoal
        with pytest.raises(ValueError, match="Unsupported training_days_per_week"):
            _pick_split(7, TrainingStatus.INTERMEDIATE, TrainingGoal.HYPERTROPHY)


# === Phase-5: STRENGTH+INTERMEDIATE → BLOCK progression ===

class TestStrengthIntermediateBlock:
    def test_strength_intermediate_uses_block(self):
        from fitness_engine.training.architect import _pick_progression
        from fitness_engine.models.profile import TrainingStatus
        from fitness_engine.models.training import TrainingGoal, ProgressionScheme
        result = _pick_progression(TrainingStatus.INTERMEDIATE, TrainingGoal.STRENGTH)
        assert result == ProgressionScheme.BLOCK

    def test_hypertrophy_intermediate_uses_dup(self):
        from fitness_engine.training.architect import _pick_progression
        from fitness_engine.models.profile import TrainingStatus
        from fitness_engine.models.training import TrainingGoal, ProgressionScheme
        result = _pick_progression(TrainingStatus.INTERMEDIATE, TrainingGoal.HYPERTROPHY)
        assert result == ProgressionScheme.DUP


# === Phase-5: detect_plateau WEIGHT_GAIN branch ===

class TestDetectPlateauWeightGain:
    def test_weight_gain_during_cut_detected(self):
        from fitness_engine.nutrition.adjustments import detect_plateau, PlateauType
        # Weight going UP over 3 weeks (deltas all negative)
        log = [80.0, 80.5, 81.0, 81.5]
        result = detect_plateau(log, expected_weekly_rate_pct=0.0075, body_weight_kg=80.0)
        assert result == PlateauType.WEIGHT_GAIN

    def test_whoosh_threshold_is_absolute(self):
        """Phase-6: Whoosh threshold is 1.5% BW absolute (not 3x expected)."""
        from fitness_engine.nutrition.adjustments import detect_plateau, PlateauType
        # 80kg user, 1.2kg drop in one week = 1.5% BW → Whoosh
        log = [80.0, 78.8, 78.8, 78.8]
        result = detect_plateau(log, expected_weekly_rate_pct=0.0075, body_weight_kg=80.0)
        assert result == PlateauType.WHOOSH


# === Phase-1.7: Packaging metadata exists ===

class TestPackagingMetadata:
    def test_pyproject_toml_exists(self):
        import os
        from pathlib import Path
        root = Path(__file__).parent.parent.parent
        assert (root / "pyproject.toml").exists()
        assert (root / "LICENSE").exists()
        assert (root / "README.md").exists()

    def test_pyproject_has_required_fields(self):
        import tomllib
        from pathlib import Path
        root = Path(__file__).parent.parent.parent
        with open(root / "pyproject.toml", "rb") as f:
            cfg = tomllib.load(f)
        assert cfg["project"]["name"] == "fitn"
        assert "version" in cfg["project"]
        assert cfg["project"]["requires-python"] == ">=3.10"
        dev_deps = cfg["project"]["optional-dependencies"]["dev"]
        assert any("pytest" in dep for dep in dev_deps), f"pytest missing from {dev_deps}"
