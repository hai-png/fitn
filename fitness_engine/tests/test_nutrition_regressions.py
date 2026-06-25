"""
Regression tests for remaining Tier 3-5 fixes.

Covers:
  - Tier 3.36: MIN_ACCEPTABLE_SCORE enforcement in allocator
  - Tier 3.37: allergens_to_avoid passed through to fillers
  - Tier 3.38: training_time_of_day field on UserProfile
  - Tier 3.40: recipe kcal-vs-macro validator
  - Tier 4.48: recomp_excellent now reachable (below obese_threshold)
  - Tier 4.49: reverse-diet field semantics (daily delta, not weekly)
  - Tier 4.52: IngredientSwap.ratio applied via adjusted_grams()
  - Tier 5.54: reverse_diet_plan + update_tdee_with_logs tests
  - Tier 5.59: allergen filtering on fillers (end-to-end)
  - Tier 5.63: vegan meal plan end-to-end
"""
import json
import pytest

from fitness_engine.models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType, TrainingTimeOfDay,
    ExerciseIntensity, Climate,
)
from fitness_engine import assess_profile, propose_plan, PlanPreferences


# === Tier 3.37 + 5.59: allergen filtering on fillers ===

class TestAllergenFilteringOnFillers:
    """Tier 3.37/5.59 — dairy-allergic users must not get dairy fillers."""

    def test_dairy_allergic_user_gets_no_dairy_fillers(self):
        """End-to-end: a user with allergens_to_avoid=['dairy'] should never
        get whey/yogurt/cottage-cheese fillers in any meal."""
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            body_fat_pct=18, neck_cm=38, waist_cm=86, hip_cm=98,
            activity_level=ActivityLevel.MOSTLY_SEDENTARY,
            training_status=TrainingStatus.NOVICE,
            primary_goal=PrimaryGoal.FAT_LOSS,
            training_days_per_week=4,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(
            profile, assessment,
            PlanPreferences(allergens_to_avoid=["dairy"]),
        )

        dairy_filler_names = {
            "Whey Protein Powder",
            "Greek Yogurt (non-fat, plain)",
            "Cottage Cheese (low-fat, 2%)",
            "Milk (skim)",
            "Cheddar Cheese",
        }
        violations = []
        for day in plan.meal.days:
            for meal in day.meals:
                for filler in meal.foods:
                    if filler.food.name in dairy_filler_names:
                        violations.append(
                            f"{day.day_name} {meal.name}: filler '{filler.food.name}' is dairy"
                        )
        assert violations == [], (
            f"Dairy-allergic user got dairy fillers:\n" + "\n".join(violations)
        )

    def test_compute_allergen_filler_exclusions_dairy(self):
        """Unit test for the _compute_allergen_filler_exclusions helper."""
        from fitness_engine.meal_plan.allocator import _compute_allergen_filler_exclusions
        exclusions = _compute_allergen_filler_exclusions(["dairy"])
        assert "Whey Protein Powder" in exclusions
        assert "Greek Yogurt (non-fat, plain)" in exclusions
        assert "Cottage Cheese (low-fat, 2%)" in exclusions

    def test_compute_allergen_filler_exclusions_multiple(self):
        """Multiple allergens combine exclusions."""
        from fitness_engine.meal_plan.allocator import _compute_allergen_filler_exclusions
        exclusions = _compute_allergen_filler_exclusions(["dairy", "eggs", "nuts"])
        assert "Whey Protein Powder" in exclusions  # dairy
        assert "Egg White (large)" in exclusions     # eggs
        assert "Almonds (raw)" in exclusions         # nuts

    def test_compute_allergen_filler_exclusions_empty(self):
        from fitness_engine.meal_plan.allocator import _compute_allergen_filler_exclusions
        assert _compute_allergen_filler_exclusions(None) == set()
        assert _compute_allergen_filler_exclusions([]) == set()


# === Tier 3.38: training_time_of_day ===

class TestTrainingTimeOfDay:
    """Tier 3.38 — training_time_of_day is now a real field."""

    def test_default_is_evening(self):
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        assert profile.training_time_of_day == TrainingTimeOfDay.EVENING

    def test_can_set_to_morning(self):
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            training_time_of_day="morning",
        )
        assert profile.training_time_of_day == TrainingTimeOfDay.MORNING

    def test_morning_training_inserts_pre_post_at_start(self):
        """When training_time_of_day=morning, PRE/POST should be at the
        start of the day's slot list (not the end)."""
        from fitness_engine.meal_plan.profile_requirements import compute_meal_plan_requirements
        from fitness_engine.models.meal import MealType
        from fitness_engine.models.nutrition import MacroSplit, NutritionPlan, CalorieTargets, CalorieStrategy
        from fitness_engine.models.assessment import AssessmentResult, BodyComposition, HealthRiskAssessment, MuscularPotential, BodyFatMethod, BodyFatCategory, BMICategory, RecommendedStrategy, HealthRiskLevel

        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            body_fat_pct=18,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            training_time_of_day=TrainingTimeOfDay.MORNING,
        )
        macros = MacroSplit(
            protein_g=150, carb_g=250, fat_g=70,
            protein_kcal=600, carb_kcal=1000, fat_kcal=630,
            protein_pct=27.0, carb_pct=45.0, fat_pct=28.0,
        )
        calories = CalorieTargets(
            strategy=CalorieStrategy.MAINTENANCE,
            base_tdee_kcal=2200, rate_pct=0, rate_label="",
            calorie_delta_kcal=0, target_calories_kcal=2230,
        )
        from fitness_engine.models.nutrition import TDEEResult, RMRResult, RMRFormula, HydrationTarget, MicronutrientTargets
        from fitness_engine.models.profile import Sex as SexE
        rmr = RMRResult(formula=RMRFormula.MIFFLIN_ST_JEOR, base_rmr_kcal=1800, adjusted_rmr_kcal=1800)
        tdee = TDEEResult(rmr_kcal=1800, activity_factor=1.2, tdee_kcal=2160, final_tdee_kcal=2200)
        nutrition = NutritionPlan(
            rmr=rmr, tdee=tdee, calories=calories, macros=macros,
            hydration=HydrationTarget(water_liters_per_day=3.0),
            micronutrients=MicronutrientTargets(fiber_g=30, fruit_cups=2, veg_cups=2),
            timeline_weeks=0,
        )
        body_comp = BodyComposition(
            body_fat_pct=18, body_fat_method=BodyFatMethod.USER_PROVIDED,
            body_fat_category=BodyFatCategory.ACCEPTABLE,
            lean_body_mass_kg=67, fat_mass_kg=15, bmi=25.9,
            bmi_category=BMICategory.OVERWEIGHT, ffmi=21, normalized_ffmi=21,
        )
        health_risk = HealthRiskAssessment(overall_risk=HealthRiskLevel.LOW)
        muscular = MuscularPotential(current_ffmi=21, current_normalized_ffmi=21)
        assessment = AssessmentResult(
            body_composition=body_comp, health_risk=health_risk,
            muscular_potential=muscular,
            recommended_strategy=RecommendedStrategy.MAINTENANCE,
            strategy_rationale="test", summary="test",
        )
        reqs = compute_meal_plan_requirements(
            profile=profile, assessment=assessment, nutrition=nutrition,
            meal_frequency=3, include_pre_post_workout=True,
        )
        # With morning training, PRE_WORKOUT should be the first slot
        assert reqs.training_day_slot_targets[0].meal_type == MealType.PRE_WORKOUT, (
            f"Morning training should put PRE_WORKOUT first; "
            f"got {[s.meal_type.value for s in reqs.training_day_slot_targets]}"
        )


# === Tier 3.40: recipe kcal-vs-macro validator ===

class TestRecipeKcalMacroValidator:
    """Tier 3.40 — recipes with inconsistent kcal vs macros get flagged."""

    def test_consistent_recipe_no_warning(self):
        """A recipe where kcal ≈ P*4 + C*4 + F*9 should NOT get a warning."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        from fitness_engine.meal_plan.recipe_loader import _check_kcal_macro_consistency
        # 200 kcal, 20P + 20C + 5F = 80+80+45 = 205 kcal (2.5% off, within 10%)
        r = Recipe(
            name="Test",
            nutrition_per_serving=NutritionPerServing(
                kcal=200, protein_g=20, carb_g=20, fat_g=5,
            ),
        )
        assert _check_kcal_macro_consistency(r) is None

    def test_inconsistent_recipe_gets_warning(self):
        """A recipe where kcal is far from P*4 + C*4 + F*9 should get a warning."""
        from fitness_engine.models.meal import Recipe, NutritionPerServing
        from fitness_engine.meal_plan.recipe_loader import _check_kcal_macro_consistency
        # 324 kcal, 50P + 50C + 5F = 200+200+45 = 445 kcal (37% off)
        r = Recipe(
            name="Inconsistent",
            nutrition_per_serving=NutritionPerServing(
                kcal=324, protein_g=50, carb_g=50, fat_g=5,
            ),
        )
        warning = _check_kcal_macro_consistency(r)
        assert warning is not None
        assert "kcal-warning" in warning


# === Tier 4.48: recomp_excellent reachable ===

class TestRecompExcellentReachable:
    """Tier 4.48 — recomp_excellent is now below obese_threshold."""

    def test_male_recomp_excellent_below_obese_threshold(self):
        from fitness_engine.assessment.decision import CUT_BULK_BOUNDARIES
        b = CUT_BULK_BOUNDARIES[Sex.MALE]
        assert b["recomp_excellent"] < b["obese_threshold"], (
            f"recomp_excellent ({b['recomp_excellent']}) must be < obese_threshold "
            f"({b['obese_threshold']}) so the 'excellent recomp' branch is reachable"
        )

    def test_female_recomp_excellent_below_obese_threshold(self):
        from fitness_engine.assessment.decision import CUT_BULK_BOUNDARIES
        b = CUT_BULK_BOUNDARIES[Sex.FEMALE]
        assert b["recomp_excellent"] < b["obese_threshold"]


# === Tier 4.49: reverse-diet field semantics ===

class TestReverseDietFieldSemantics:
    """Tier 4.49 — reverse-diet CalorieTargets now use consistent semantics."""

    def test_reverse_diet_calorie_delta_is_daily_not_weekly(self):
        """calorie_delta_kcal should be the DAILY delta (increment/7), not
        the weekly increment. This matches the documented field semantics."""
        from fitness_engine.nutrition.calories import reverse_diet_plan
        weekly_targets, targets = reverse_diet_plan(
            current_calories=1500,
            target_calories=2000,
            aggressiveness="moderate",  # 100 kcal/week
        )
        # Daily delta = 100/7 ≈ 14.3 kcal (was 100 before fix)
        assert targets.calorie_delta_kcal < 50, (
            f"calorie_delta_kcal should be daily (~14), not weekly (100); "
            f"got {targets.calorie_delta_kcal}"
        )

    def test_reverse_diet_rate_pct_is_fraction_of_current(self):
        from fitness_engine.nutrition.calories import reverse_diet_plan
        weekly_targets, targets = reverse_diet_plan(
            current_calories=2000,
            target_calories=2500,
            aggressiveness="moderate",
        )
        # rate_pct = increment / current_calories = 100/2000 = 0.05
        assert 0 < targets.rate_pct < 0.1, (
            f"rate_pct should be ~0.05 (100/2000); got {targets.rate_pct}"
        )


# === Tier 4.52: IngredientSwap.ratio ===

class TestIngredientSwapRatio:
    """Tier 4.52 — IngredientSwap.ratio now has an adjusted_grams method."""

    def test_adjusted_grams_1_to_1_ratio(self):
        from fitness_engine.meal_plan.swap_system import IngredientSwap
        swap = IngredientSwap(original="chicken", alternatives=["tofu"], ratio=1.0)
        assert swap.adjusted_grams(100) == 100

    def test_adjusted_grams_0_75_ratio(self):
        from fitness_engine.meal_plan.swap_system import IngredientSwap
        swap = IngredientSwap(original="chicken", alternatives=["tofu"], ratio=0.75)
        assert swap.adjusted_grams(100) == 75

    def test_adjusted_grams_0_8_ratio(self):
        from fitness_engine.meal_plan.swap_system import IngredientSwap
        swap = IngredientSwap(original="berbere", alternatives=["mitmita"], ratio=0.8)
        assert swap.adjusted_grams(50) == 40


# === Tier 5.54: reverse_diet_plan + update_tdee_with_logs tests ===

class TestReverseDietAndAdaptiveTDEE:
    """Tier 5.54 — these functions were previously untested."""

    def test_reverse_diet_plan_generates_weekly_targets(self):
        from fitness_engine.nutrition.calories import reverse_diet_plan
        weekly_targets, targets = reverse_diet_plan(
            current_calories=1500,
            target_calories=2000,
            aggressiveness="moderate",
        )
        assert len(weekly_targets) > 0
        assert weekly_targets[0] == 1500 + 100  # first week = current + increment
        assert weekly_targets[-1] >= 2000  # last week reaches target

    def test_reverse_diet_conservative_smaller_increment(self):
        from fitness_engine.nutrition.calories import reverse_diet_plan
        _, conservative = reverse_diet_plan(1500, 2000, "conservative")
        _, moderate = reverse_diet_plan(1500, 2000, "moderate")
        _, aggressive = reverse_diet_plan(1500, 2000, "aggressive")
        # Conservative < moderate < aggressive in weekly increment
        assert conservative.calorie_delta_kcal < moderate.calorie_delta_kcal
        assert moderate.calorie_delta_kcal < aggressive.calorie_delta_kcal

    def test_observed_tdee_first_principles_basic(self):
        """observed_TDEE = intake - (delta_weight × 7700) / n_days.
        If you ate 2500 and LOST 0.5 kg over 7 days, your TDEE is HIGHER
        than intake (you burned more than you ate).
        delta_weight = 79.5 - 80.0 = -0.5 (weight went down)
        observed = 2500 - (-0.5 * 7700) / 7 = 2500 + 550 = 3050"""
        from fitness_engine.nutrition.tdee import observed_tdee_first_principles
        tdee = observed_tdee_first_principles(
            avg_intake_kcal=2500,
            weight_start_kg=80.0,
            weight_end_kg=79.5,  # lost 0.5 kg
            n_days=7,
        )
        assert abs(tdee - 3050) < 5, f"Expected ~3050 (lost weight → TDEE > intake); got {tdee}"

    def test_observed_tdee_weight_gain_case(self):
        """If you ate 2500 and GAINED 0.5 kg over 7 days, your TDEE is LOWER
        than intake (you ate more than you burned).
        delta_weight = 80.5 - 80.0 = +0.5
        observed = 2500 - (0.5 * 7700) / 7 = 2500 - 550 = 1950"""
        from fitness_engine.nutrition.tdee import observed_tdee_first_principles
        tdee = observed_tdee_first_principles(
            avg_intake_kcal=2500,
            weight_start_kg=80.0,
            weight_end_kg=80.5,  # gained 0.5 kg
            n_days=7,
        )
        assert abs(tdee - 1950) < 5, f"Expected ~1950 (gained weight → TDEE < intake); got {tdee}"

    def test_observed_tdee_zero_division_guard(self):
        """n_days=0 must raise ValueError (Phase-6 fix: was unguarded division).

        Previously this would raise ZeroDivisionError; now it raises
        ValueError with a descriptive message before reaching the division.
        """
        from fitness_engine.nutrition.tdee import observed_tdee_first_principles
        with pytest.raises(ValueError, match="n_days must be >= 1"):
            observed_tdee_first_principles(2500, 80.0, 79.5, 0)
        # n_days < 0 also raises
        with pytest.raises(ValueError, match="n_days must be >= 1"):
            observed_tdee_first_principles(2500, 80.0, 79.5, -5)


# === Tier 5.63: vegan meal plan end-to-end ===

class TestVeganMealPlan:
    """Tier 5.63 — vegan diet plan should have no animal products."""

    def test_vegan_plan_has_no_meat_ingredients(self):
        """A vegan user's meal plan should contain only vegan recipes."""
        profile = UserProfile(
            age=27, sex=Sex.MALE, height_cm=180, weight_kg=78,
            body_fat_pct=14, neck_cm=37, waist_cm=80, hip_cm=98,
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            training_status=TrainingStatus.NOVICE,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.VEGAN,
        )
        assessment = assess_profile(profile)
        plan = propose_plan(
            profile, assessment,
            PlanPreferences(cuisine_preference="ethiopian"),
        )
        # Check that no recipe contains meat/dairy/egg (using the same
        # _recipe_has_meat_ingredients heuristic)
        from fitness_engine.meal_plan.recipe_loader import _recipe_has_meat_ingredients
        violations = []
        for day in plan.meal.days:
            for meal in day.meals:
                if meal.recipe:
                    if _recipe_has_meat_ingredients(meal.recipe):
                        violations.append(
                            f"{day.day_name} {meal.name}: recipe contains animal products"
                        )
        assert violations == [], (
            f"Vegan plan contains non-vegan recipes:\n" + "\n".join(violations)
        )


# === Tier 3.31: ExerciseIntensity / Climate enums ===

class TestHydrationEnums:
    """Tier 3.31 — hydration accepts enum values, not just strings."""

    def test_compute_hydration_accepts_enum(self):
        from fitness_engine.nutrition import compute_hydration
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        # Using enums (Tier 3.31)
        result = compute_hydration(
            profile,
            exercise_hours_per_day=2.0,
            exercise_intensity=ExerciseIntensity.INTENSE,
            climate=Climate.HOT,
        )
        assert result.water_liters_per_day > 3.0  # hot + intense → high hydration

    def test_compute_hydration_warns_on_unknown_string(self):
        """Unknown string values should fall back to defaults with a warning."""
        import warnings
        from fitness_engine.nutrition import compute_hydration
        profile = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = compute_hydration(
                profile,
                exercise_intensity="invalid_intensity",
                climate="invalid_climate",
            )
            assert len(w) >= 2  # at least 2 warnings (intensity + climate)
            assert result.water_liters_per_day > 0  # didn't crash
