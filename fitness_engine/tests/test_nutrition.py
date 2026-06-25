"""Unit tests for the nutrition module."""
import pytest

from fitness_engine.models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType, CutRateTier,
)
from fitness_engine.models.assessment import (
    AssessmentResult, BodyComposition, HealthRiskAssessment,
    MuscularPotential, RecommendedStrategy,
)
from fitness_engine.nutrition import (
    rmr_mifflin_st_jeor, rmr_harris_benedict_original, rmr_cunningham,
    compute_rmr, compute_tdee, adaptive_tdee, observed_tdee_first_principles,
    cut_target_calories, bulk_target_calories,
    maintenance_target_calories, recomp_target_calories,
    compute_macros, compute_hydration, compute_micronutrients,
    MIN_CALORIES, MAX_WEEKLY_LOSS_PCT, BULK_RATE_BY_STATUS,
    cut_macro_adjustment, bulk_macro_adjustment,
    build_nutrition_plan,
)


# === Fixtures ===

@pytest.fixture
def male_profile():
    return UserProfile(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
        body_fat_pct=18, neck_cm=38, waist_cm=86, hip_cm=98,
        activity_level=ActivityLevel.MOSTLY_SEDENTARY,
        training_status=TrainingStatus.NOVICE,
        primary_goal=PrimaryGoal.FAT_LOSS,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def female_profile():
    return UserProfile(
        age=28, sex=Sex.FEMALE, height_cm=165, weight_kg=65,
        body_fat_pct=25, neck_cm=32, waist_cm=70, hip_cm=95,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.BEGINNER,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=3,
        equipment_access=EquipmentAccess.FULL_GYM,
        diet_type=DietType.OMNIVORE,
    )


@pytest.fixture
def male_assessment(male_profile):
    """Build a minimal AssessmentResult for testing the nutrition module."""
    bc = BodyComposition(
        body_fat_pct=18, body_fat_method="user_provided",
        body_fat_category="acceptable",
        lean_body_mass_kg=67.2, fat_mass_kg=14.8,
        bmi=25.9, bmi_category="overweight",
        ffmi=21.2, normalized_ffmi=21.3,
    )
    hr = HealthRiskAssessment()
    mp = MuscularPotential(
        current_ffmi=21.2, current_normalized_ffmi=21.3,
        headroom_kg=8.0, expected_monthly_muscle_gain_kg=0.7,
    )
    return AssessmentResult(
        body_composition=bc, health_risk=hr, muscular_potential=mp,
        recommended_strategy=RecommendedStrategy.CUT,
        strategy_rationale="test",
        summary="test",
    )


# === RMR tests ===

class TestRMR:
    def test_mifflin_male(self, male_profile):
        # Men: 9.99*82 + 6.25*178 - 4.92*30 + 5 = 819.18 + 1112.5 - 147.6 + 5 = 1789.08
        rmr = rmr_mifflin_st_jeor(male_profile)
        assert abs(rmr - 1789) < 5

    def test_mifflin_female(self, female_profile):
        # Women: 9.99*65 + 6.25*165 - 4.92*28 - 161 = 649.35 + 1031.25 - 137.76 - 161 = 1381.84
        rmr = rmr_mifflin_st_jeor(female_profile)
        assert abs(rmr - 1382) < 5

    def test_cunningham_uses_ffm(self, male_profile):
        """Tier 2.10 fix: rmr_cunningham now implements the REAL Cunningham (1991)
        formula: RMR = 500 + 22 × FFM. Previously it implemented Katch-McArdle
        (370 + 21.6 × LBM) under the wrong name."""
        # Cunningham: 500 + 22 * FFM
        # FFM = 82 * (1 - 0.18) = 67.24
        # RMR = 500 + 22 * 67.24 = 500 + 1479.28 = 1979.28
        rmr = rmr_cunningham(male_profile, body_fat_pct=18)
        assert abs(rmr - 1979) < 5, (
            f"Real Cunningham (500 + 22*FFM) should give ~1979; got {rmr}. "
            f"Previously this test asserted 1822 (the Katch-McArdle value) — that was the bug."
        )

    def test_katch_mcardle_uses_lbm(self, male_profile):
        """Tier 2.10 fix: rmr_katch_mcardle implements Katch-McArdle (1975):
        RMR = 370 + 21.6 × LBM. This is the formula that was previously
        mislabeled as 'Cunningham'."""
        # Katch-McArdle: 370 + 21.6 * LBM
        # LBM = 82 * (1 - 0.18) = 67.24
        # RMR = 370 + 21.6 * 67.24 = 370 + 1452.4 = 1822.4
        from fitness_engine.nutrition import rmr_katch_mcardle
        rmr = rmr_katch_mcardle(male_profile, body_fat_pct=18)
        assert abs(rmr - 1822) < 5

    def test_cunningham_rejects_invalid_body_fat_pct(self, male_profile):
        """Tier 2.10 fix: body_fat_pct outside [2, 60] must raise ValueError
        to prevent negative-LBM nonsense."""
        with pytest.raises(ValueError):
            rmr_cunningham(male_profile, body_fat_pct=150)
        with pytest.raises(ValueError):
            rmr_cunningham(male_profile, body_fat_pct=-5)
        with pytest.raises(ValueError):
            rmr_cunningham(male_profile, body_fat_pct=0)

    def test_select_rmr_formula_uses_passed_body_fat_pct(self, male_profile):
        """Tier 2.11 fix: select_rmr_formula must consult the body_fat_pct
        parameter, not just profile.body_fat_pct. Previously, a user with
        profile.body_fat_pct=None but an assessment-derived BF% would
        silently get Mifflin-St Jeor instead of Katch-McArdle."""
        from fitness_engine.nutrition import select_rmr_formula
        from fitness_engine.models.nutrition import RMRFormula
        # Profile with no body_fat_pct
        male_profile.body_fat_pct = None
        # But assessment-derived BF% passed in
        formula = select_rmr_formula(male_profile, body_fat_pct=18)
        assert formula == RMRFormula.KATCH_MCARDLE, (
            f"select_rmr_formula should return KATCH_MCARDLE when body_fat_pct "
            f"is passed, even if profile.body_fat_pct is None; got {formula}"
        )

    def test_compute_rmr_uses_katch_mcardle_when_bf_provided(self, male_profile):
        """Tier 2.10/2.11 regression: when body_fat_pct is passed to compute_rmr,
        the result.formula should be KATCH_MCARDLE (not CUNNINGHAM)."""
        male_profile.body_fat_pct = None  # force use of passed BF%
        result = compute_rmr(male_profile, body_fat_pct=18)
        from fitness_engine.models.nutrition import RMRFormula
        assert result.formula == RMRFormula.KATCH_MCARDLE, (
            f"compute_rmr should use KATCH_MCARDLE when BF% is provided; "
            f"got {result.formula}"
        )

    def test_compute_rmr_with_adaptation(self, male_profile):
        result = compute_rmr(
            male_profile, body_fat_pct=18,
            in_active_deficit=True, weight_reduced_pct=0.12,
        )
        # Base 1822 * 0.95 (deficit) * 0.97 (weight-reduced) = 1679
        assert result.adjusted_rmr_kcal < result.base_rmr_kcal
        assert abs(result.adjusted_rmr_kcal - 1679) < 20


# === TDEE tests ===

class TestTDEE:
    def test_tdee_mostly_sedentary_male(self, male_profile):
        rmr_result = compute_rmr(male_profile, body_fat_pct=18)
        tdee = compute_tdee(rmr_result, male_profile)
        # Mostly sedentary = ×1.45
        # 1822 * 1.45 = 2642
        assert abs(tdee.tdee_kcal - 2642) < 30
        assert tdee.activity_factor == 1.45


# === Adaptive TDEE tests ===

class TestAdaptiveTDEE:
    def test_first_principles_weight_stable(self):
        # If weight stable, observed TDEE = avg intake
        tdee = observed_tdee_first_principles(
            avg_intake_kcal=2500,
            weight_start_kg=80, weight_end_kg=80, n_days=14,
        )
        assert tdee == 2500

    def test_first_principles_losing_weight(self):
        # If losing 0.5 kg/week, observed TDEE > intake
        # 0.5 kg/wk = 0.5/7 kg/day
        # observed_TDEE = 2000 - (-0.5/7 * 7700 / 1) = 2000 + 550 = 2550
        # But for 14 days at 0.5 kg/wk = 1 kg total
        tdee = observed_tdee_first_principles(
            avg_intake_kcal=2000,
            weight_start_kg=80, weight_end_kg=79, n_days=14,
        )
        # Δweight = -1 kg, observed_TDEE = 2000 - (-1 * 7700) / 14 = 2000 + 550 = 2550
        assert abs(tdee - 2550) < 1

    def test_adaptive_weight_data_ramp(self):
        from fitness_engine.nutrition.tdee import adaptive_weight_data
        assert adaptive_weight_data(0) == 0
        assert adaptive_weight_data(7) == 0
        assert adaptive_weight_data(30) > 0
        assert adaptive_weight_data(60) == 1.0
        assert adaptive_weight_data(100) == 1.0

    def test_adaptive_tdee_blend_at_day_0(self):
        # At 0 days, should return prior
        result = adaptive_tdee(
            prior_tdee=2500, avg_intake_kcal=2000,
            weight_start_kg=80, weight_end_kg=80, n_days=0,
        )
        assert result == 2500


# === Calorie target tests ===

class TestCalorieTargets:
    def test_cut_target_uses_default_rate(self, male_profile):
        target = cut_target_calories(male_profile, tdee_kcal=2500)
        # 0.75% of 82 kg = 0.615 kg/wk
        # deficit = 0.615 * 1100 = 676.5 kcal/day
        # target = 2500 - 676.5 = 1823.5
        assert target.target_calories_kcal < 2500
        assert target.calorie_delta_kcal < 0
        assert "0.75%" in target.rate_label or "0.50%" in target.rate_label

    def test_cut_respects_calorie_floor(self):
        # Very small woman with aggressive cut
        p = UserProfile(
            age=30, sex=Sex.FEMALE, height_cm=150, weight_kg=45,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.FAT_LOSS,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
            cut_rate_tier=CutRateTier.AGGRESSIVE,
        )
        target = cut_target_calories(p, tdee_kcal=1400)
        # Should not drop below 1200 for women
        assert target.target_calories_kcal >= 1200
        assert target.calorie_floor_applied

    def test_bulk_target_uses_training_status(self, male_profile):
        # Novice bulk rate = 1.5% BW/month
        target = bulk_target_calories(male_profile, tdee_kcal=2500)
        # 1.5% of 82 = 1.23 kg/mo
        # surplus = 1.23 * 330 = 406 kcal/day
        # target = 2500 + 406 = 2906
        assert target.target_calories_kcal > 2500
        assert "1.50%" in target.rate_label

    def test_maintenance_target(self):
        target = maintenance_target_calories(tdee_kcal=2500)
        assert target.target_calories_kcal == 2500
        assert target.calorie_delta_kcal == 0

    def test_recomp_target_high_potential(self, male_profile):
        # BF=18% → moderate recomp potential (15-25%)
        target = recomp_target_calories(male_profile, tdee_kcal=2500, body_fat_pct=18)
        # 5% deficit
        assert target.target_calories_kcal < 2500
        assert target.target_calories_kcal > 2200

    def test_max_cut_rate_enforced(self, male_profile):
        """Tier 5.65 fix: previously this test only asserted the rate was capped,
        but did NOT verify the user is warned (the Tier 2.14 fix added a cap
        warning note). Now we assert both the cap AND the warning."""
        # Try an absurdly high rate
        target = cut_target_calories(male_profile, tdee_kcal=3000, rate_pct=0.05)
        # Should be capped at MAX_WEEKLY_LOSS_PCT = 1.5%
        assert target.rate_pct <= MAX_WEEKLY_LOSS_PCT
        # Tier 5.65: verify the user is warned that their requested rate was clipped
        notes_str = " ".join(target.notes)
        assert "clipped" in notes_str.lower() or "cap" in notes_str.lower(), (
            f"User should be warned when requested rate is clipped to safety cap. "
            f"Notes: {target.notes}"
        )


# === Macro tests ===

class TestMacros:
    def test_macros_sum_to_total(self, male_profile, male_assessment):
        from fitness_engine.nutrition.calories import cut_target_calories
        targets = cut_target_calories(male_profile, tdee_kcal=2500)
        macros = compute_macros(
            male_profile, body_fat_pct=18,
            strategy=RecommendedStrategy.CUT,
            calorie_targets=targets,
        )
        total_kcal = macros.protein_kcal + macros.fat_kcal + macros.carb_kcal
        assert abs(total_kcal - targets.target_calories_kcal) < 50   # ±50 kcal rounding

    def test_protein_set_for_cut(self, male_profile, male_assessment):
        from fitness_engine.nutrition.calories import cut_target_calories
        targets = cut_target_calories(male_profile, tdee_kcal=2500)
        macros = compute_macros(
            male_profile, body_fat_pct=18,
            strategy=RecommendedStrategy.CUT,
            calorie_targets=targets,
        )
        # Cut: 1.14 g/lb LBM × 67.2 kg × 2.2046 = 1.14 × 148.15 = ~168.9 g
        assert abs(macros.protein_g - 169) < 5

    def test_fat_within_range_for_cut(self, male_profile):
        from fitness_engine.nutrition.calories import cut_target_calories
        targets = cut_target_calories(male_profile, tdee_kcal=2500)
        macros = compute_macros(
            male_profile, body_fat_pct=18,
            strategy=RecommendedStrategy.CUT,
            calorie_targets=targets,
        )
        # Cut fat % should be 15-25%
        assert 12 <= macros.fat_pct <= 28   # allow some rounding tolerance


# === Hydration tests ===

class TestHydration:
    def test_base_hydration_male(self, male_profile):
        h = compute_hydration(male_profile, exercise_hours_per_day=0,
                              exercise_intensity="light", climate="temperate")
        # 82 * 0.030 + 0.3 = 2.76 L
        assert abs(h.water_liters_per_day - 2.76) < 0.1

    def test_exercise_adds_water(self, male_profile):
        h1 = compute_hydration(male_profile, exercise_hours_per_day=0,
                               exercise_intensity="moderate", climate="temperate")
        h2 = compute_hydration(male_profile, exercise_hours_per_day=1,
                               exercise_intensity="moderate", climate="temperate")
        # 1 hour moderate = +0.5 L
        assert h2.water_liters_per_day > h1.water_liters_per_day
        assert abs(h2.water_liters_per_day - h1.water_liters_per_day - 0.5) < 0.05

    def test_hot_climate_increases_water(self, male_profile):
        h_cold = compute_hydration(male_profile, climate="cold")
        h_hot = compute_hydration(male_profile, climate="hot")
        assert h_hot.water_liters_per_day > h_cold.water_liters_per_day


# === Micronutrient tests ===

class TestMicronutrients:
    def test_fiber_scales_with_calories(self):
        m1 = compute_micronutrients(2000)
        m2 = compute_micronutrients(3000)
        # 14 g per 1000 kcal
        assert abs(m1.fiber_g - 28) < 1
        assert abs(m2.fiber_g - 42) < 1

    def test_fruit_veg_tiers(self):
        m_low = compute_micronutrients(1500)
        m_mid = compute_micronutrients(2500)
        m_high = compute_micronutrients(3500)
        assert m_low.fruit_cups == 2
        assert m_mid.fruit_cups == 3
        assert m_high.fruit_cups == 4


# === Macro adjustment tests ===

class TestMacroAdjustments:
    def test_cut_adjustment_2_to_1_ratio(self):
        # 250 kcal cut → ~-41.67g carbs, ~-9.26g fat (2:1 by calories)
        # 2/3 * 250 = 166.67 kcal / 4 = 41.67g carbs
        # 1/3 * 250 = 83.33 kcal / 9 = 9.26g fat
        carb_g, fat_g, _ = cut_macro_adjustment(-250)
        assert abs(carb_g - (-41.67)) < 0.5
        assert abs(fat_g - (-9.26)) < 0.5
        # Verify the 2:1 ratio by calories
        carb_kcal = abs(carb_g) * 4
        fat_kcal = abs(fat_g) * 9
        assert abs(carb_kcal / fat_kcal - 2.0) < 0.05

    def test_bulk_adjustment_3_to_1_ratio(self):
        # 300 kcal bulk → +56g carbs, +8g fat (approx)
        # 3/4 * 300 = 225 kcal from carbs → 56.25 g
        # 1/4 * 300 = 75 kcal from fat → 8.33 g
        carb_g, fat_g, _ = bulk_macro_adjustment(300)
        assert abs(carb_g - 56) < 1
        assert abs(fat_g - 8) < 1


# === Integration test ===

class TestNutritionPlan:
    def test_build_nutrition_plan(self, male_profile, male_assessment):
        plan = build_nutrition_plan(male_profile, male_assessment)
        assert plan.rmr is not None
        assert plan.tdee is not None
        assert plan.calories is not None
        assert plan.macros is not None
        assert plan.hydration is not None
        assert plan.micronutrients is not None
        assert plan.timeline_weeks > 0
        assert plan.calories.target_calories_kcal > 0

    def test_nutrition_plan_to_dict(self, male_profile, male_assessment):
        plan = build_nutrition_plan(male_profile, male_assessment)
        d = plan.to_dict()
        import json
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 100
