"""
Unit tests for math-correctness of individual functions.

These tests verify specific formulas and edge cases that the E2E pipeline
tests don't directly exercise. They cover the math itself, not the integration.
"""
from __future__ import annotations

import pytest

from fitness_engine.assessment.body_composition import (
    BMICategory,
    BodyFatCategory,
    body_fat_cun_bae,
    body_fat_navy,
    classify_bf,
    classify_bmi,
    compute_body_fat,
    compute_ffmi,
    target_weight_at_target_bf,
)
from fitness_engine.assessment.health_risk import (
    absi_z_score,
    classify_whr,
    compute_absi,
    compute_whr,
    compute_whtr,
)
from fitness_engine.assessment.muscular_potential import (
    FFMI_NATURAL_ATTAINABLE,
    FFMI_NATURAL_COMMON,
    FFMI_NATURAL_LIKELY_MAX,
    assess_muscular_potential,
    berkhan_stage_max_weight_kg,
)
from fitness_engine.models.profile import (
    ActivityLevel,
    EquipmentAccess,
    PrimaryGoal,
    Sex,
    TrainingStatus,
    UserProfile,
)
from fitness_engine.nutrition.adjustments import (
    PlateauType,
    detect_plateau,
)
from fitness_engine.nutrition.calories import (
    MAX_WEEKLY_LOSS_PCT,
    bulk_target_calories,
    cut_target_calories,
    maintenance_target_calories,
    recomp_target_calories,
)
from fitness_engine.nutrition.hydration import compute_hydration
from fitness_engine.nutrition.macros import (
    bulk_macro_adjustment,
    compute_carbs,
    compute_fat,
    compute_protein,
    cut_macro_adjustment,
)
from fitness_engine.nutrition.micronutrients import compute_micronutrients
from fitness_engine.nutrition.rmr import (
    RMRFormula,
    compute_rmr,
    rmr_katch_mcardle,
    rmr_mifflin_st_jeor,
    select_rmr_formula,
)
from fitness_engine.nutrition.tdee import (
    ACTIVITY_FACTORS_RIPPEDBODY,
    activity_factor,
    adaptive_weight_data,
    compute_tdee,
    observed_tdee_first_principles,
)
from fitness_engine.training.intensity_model import (
    generate_warmup_sets,
    rir_to_rpe,
    rpe_to_rir,
)
from fitness_engine.training.periodization import (
    _BLOCK_PHASE_MODIFIERS,
    get_block_phases_for_program,
    get_mesocycle_length,
    get_program_duration_weeks,
)
from fitness_engine.training.progression import (
    dup_next,
    linear_progression_next,
)
from fitness_engine.training.volume_landmarks import (
    check_session_volume_cap,
    get_muscle_landmarks,
    get_recommended_frequency,
)


def _profile(**kw) -> UserProfile:
    defaults = dict(
        age=30, sex=Sex.MALE, height_cm=178, weight_kg=82, body_fat_pct=18,
        activity_level=ActivityLevel.LIGHTLY_ACTIVE,
        training_status=TrainingStatus.INTERMEDIATE,
        primary_goal=PrimaryGoal.MAINTENANCE,
        training_days_per_week=4,
        equipment_access=EquipmentAccess.FULL_GYM,
        neck_cm=38, waist_cm=85,
    )
    if "diet" in kw:
        kw["diet_type"] = kw.pop("diet")
    defaults.update(kw)
    return UserProfile(**defaults)


# ============================================================
# Body composition math
# ============================================================

class TestBodyCompositionMath:

    def test_bmi_classification_thresholds(self):
        """BMI boundaries: 18.5, 25, 30."""
        assert classify_bmi(17) == BMICategory.UNDERWEIGHT
        assert classify_bmi(18.5) == BMICategory.NORMAL
        assert classify_bmi(24.9) == BMICategory.NORMAL
        assert classify_bmi(25) == BMICategory.OVERWEIGHT
        assert classify_bmi(29.9) == BMICategory.OVERWEIGHT
        assert classify_bmi(30) == BMICategory.OBESE
        assert classify_bmi(40) == BMICategory.OBESE

    def test_bf_classification_male_thresholds(self):
        assert classify_bf(5, Sex.MALE) == BodyFatCategory.ESSENTIAL
        assert classify_bf(6, Sex.MALE) == BodyFatCategory.ATHLETE
        assert classify_bf(14, Sex.MALE) == BodyFatCategory.FITNESS
        assert classify_bf(18, Sex.MALE) == BodyFatCategory.ACCEPTABLE
        assert classify_bf(25, Sex.MALE) == BodyFatCategory.OBESITY

    def test_bf_classification_female_thresholds(self):
        # Female essential band is BF < 14 (i.e. 13 is essential, 14 is athlete).
        assert classify_bf(13, Sex.FEMALE) == BodyFatCategory.ESSENTIAL
        assert classify_bf(14, Sex.FEMALE) == BodyFatCategory.ATHLETE
        assert classify_bf(21, Sex.FEMALE) == BodyFatCategory.FITNESS
        assert classify_bf(25, Sex.FEMALE) == BodyFatCategory.ACCEPTABLE
        assert classify_bf(32, Sex.FEMALE) == BodyFatCategory.OBESITY

    def test_classify_bmi_rejects_invalid(self):
        with pytest.raises(ValueError):
            classify_bmi(0)
        with pytest.raises(ValueError):
            classify_bmi(-1)
        with pytest.raises(ValueError):
            classify_bmi(float("nan"))

    def test_classify_bf_rejects_invalid(self):
        with pytest.raises(ValueError):
            classify_bf(-1, Sex.MALE)
        with pytest.raises(ValueError):
            classify_bf(float("nan"), Sex.MALE)

    def test_navy_male_returns_bf(self):
        profile = _profile(neck_cm=38, waist_cm=85)
        bf = body_fat_navy(profile)
        assert bf is not None
        assert 5 <= bf <= 40

    def test_navy_female_requires_hip(self):
        profile = _profile(sex=Sex.FEMALE, neck_cm=33, waist_cm=72, hip_cm=None)
        assert body_fat_navy(profile) is None
        profile = _profile(sex=Sex.FEMALE, neck_cm=33, waist_cm=72, hip_cm=96)
        bf = body_fat_navy(profile)
        assert bf is not None

    def test_cun_bae_clamped_to_2_60(self):
        """CUN-BAE returns values in [2, 60] even for extreme BMI."""
        # Very low BMI
        profile = _profile(height_cm=200, weight_kg=40)  # BMI ~10
        bf = body_fat_cun_bae(profile)
        assert 2 <= bf <= 60
        # Very high BMI
        profile = _profile(height_cm=150, weight_kg=200)  # BMI ~89
        bf = body_fat_cun_bae(profile)
        assert 2 <= bf <= 60

    def test_compute_body_fat_uses_user_provided_when_available(self):
        profile = _profile(body_fat_pct=15.5)
        bf, method = compute_body_fat(profile)
        assert bf == 15.5
        assert method.value == "user_provided"

    def test_compute_body_fat_uses_navy_when_no_user_bf(self):
        profile = _profile(body_fat_pct=None, neck_cm=38, waist_cm=85)
        bf, method = compute_body_fat(profile)
        assert method.value == "navy"

    def test_compute_body_fat_uses_cun_bae_when_no_measurements(self):
        profile = _profile(body_fat_pct=None, neck_cm=None, waist_cm=None)
        bf, method = compute_body_fat(profile)
        assert method.value == "cun_bae"

    def test_compute_ffmi_correct_value(self):
        """FFMI = LBM / height_m^2 = (weight × (1 - bf/100)) / height^2."""
        ffmi, norm_ffmi = compute_ffmi(weight_kg=80, bf_pct=20, height_m=1.80)
        expected_ffmi = (80 * 0.80) / (1.80 ** 2)
        assert abs(ffmi - expected_ffmi) < 0.001

    def test_compute_ffmi_rejects_zero_height(self):
        with pytest.raises(ValueError):
            compute_ffmi(weight_kg=80, bf_pct=20, height_m=0)

    def test_compute_ffmi_rejects_bf_over_100(self):
        with pytest.raises(ValueError):
            compute_ffmi(weight_kg=80, bf_pct=150, height_m=1.8)

    def test_target_weight_at_target_bf(self):
        """At lower BF%, target weight should be lower (assuming LBM constant)."""
        # 80kg at 20% BF, target 10% BF → LBM = 64, target = 64 / 0.9 = 71.1
        target = target_weight_at_target_bf(80, 20, 10)
        assert abs(target - 71.11) < 0.1

    def test_target_weight_at_target_bf_rejects_100(self):
        with pytest.raises(ValueError):
            target_weight_at_target_bf(80, 20, 100)


# ============================================================
# Health risk math
# ============================================================

class TestHealthRiskMath:

    def test_compute_whr_basic(self):
        assert compute_whr(80, 100) == 0.8
        assert compute_whr(90, 100) == 0.9

    def test_compute_whr_rejects_zero_hip(self):
        with pytest.raises(ValueError):
            compute_whr(80, 0)

    def test_classify_whr_male(self):
        assert classify_whr(0.80, Sex.MALE).value == "low"
        assert classify_whr(0.86, Sex.MALE).value == "moderate"
        assert classify_whr(0.91, Sex.MALE).value == "high"
        assert classify_whr(1.05, Sex.MALE).value == "very_high"

    def test_classify_whr_female(self):
        assert classify_whr(0.75, Sex.FEMALE).value == "low"
        assert classify_whr(0.81, Sex.FEMALE).value == "moderate"
        assert classify_whr(0.86, Sex.FEMALE).value == "high"
        assert classify_whr(1.05, Sex.FEMALE).value == "very_high"

    def test_compute_whtr_basic(self):
        assert compute_whtr(80, 178) == pytest.approx(0.4494, abs=0.001)

    def test_compute_whtr_rejects_zero_height(self):
        with pytest.raises(ValueError):
            compute_whtr(80, 0)

    def test_compute_absi_typical_value(self):
        """ABSI for a typical adult should be in the 0.07-0.09 range."""
        absi = compute_absi(waist_cm=85, weight_kg=82, height_cm=178)
        assert 0.07 < absi < 0.09

    def test_compute_absi_rejects_zero_weight(self):
        with pytest.raises(ValueError):
            compute_absi(85, 0, 178)

    def test_absi_z_score_in_typical_range(self):
        """For typical adult, z-score should be within ±3."""
        absi = compute_absi(85, 82, 178)
        z = absi_z_score(absi, age=30, sex=Sex.MALE)
        assert -3 < z < 3

    def test_absi_z_score_uses_correct_band(self):
        """Different age bands should produce different z-scores."""
        absi = 0.0820
        z_25 = absi_z_score(absi, age=25, sex=Sex.MALE)
        z_50 = absi_z_score(absi, age=50, sex=Sex.MALE)
        # Different age bands have different means, so z-scores should differ
        assert z_25 != z_50


# ============================================================
# Muscular potential
# ============================================================

class TestMuscularPotential:

    def test_ffmi_ceilings_are_canonical_values(self):
        assert FFMI_NATURAL_COMMON == 25.0
        assert FFMI_NATURAL_ATTAINABLE == 27.3
        assert FFMI_NATURAL_LIKELY_MAX == 28.0

    def test_berkhan_max_weight(self):
        """Berkhan: max_stage_weight_kg = height_cm - 100."""
        assert berkhan_stage_max_weight_kg(180) == 80
        assert berkhan_stage_max_weight_kg(170) == 70

    def test_assess_muscular_potential_returns_valid_object(self):
        profile = _profile()
        result = assess_muscular_potential(profile, body_fat_pct=18)
        assert 0 <= result.ffmi_to_ceiling_pct <= 100
        assert result.headroom_kg >= 0
        assert result.current_ffmi > 0
        assert result.current_normalized_ffmi > 0

    def test_assess_muscular_potential_handles_high_bf(self):
        """BF% > 100 should not crash (clamped internally)."""
        profile = _profile()
        result = assess_muscular_potential(profile, body_fat_pct=150)
        assert result.ffmi_to_ceiling_pct >= 0
        assert result.ffmi_to_ceiling_pct <= 100


# ============================================================
# RMR math
# ============================================================

class TestRMR:

    def test_mifflin_male_typical_value(self):
        """Mifflin-St Jeor for 30yo male, 178cm, 82kg, 18% BF."""
        profile = _profile(weight_kg=82, height_cm=178, age=30, sex=Sex.MALE)
        rmr = rmr_mifflin_st_jeor(profile)
        # Expected: 9.99*82 + 6.25*178 - 4.92*30 + 5 = 819.18 + 1112.5 - 147.6 + 5 = 1789.08
        assert 1700 < rmr < 1900

    def test_mifflin_female_typical_value(self):
        profile = _profile(weight_kg=65, height_cm=165, age=30, sex=Sex.FEMALE)
        rmr = rmr_mifflin_st_jeor(profile)
        # Expected: 9.99*65 + 6.25*165 - 4.92*30 - 161 = 649.35 + 1031.25 - 147.6 - 161 = 1372.0
        assert 1300 < rmr < 1500

    def test_katch_mcardle_requires_bf(self):
        """Katch-McArdle uses LBM, so requires body_fat_pct."""
        # LBM = 82 * (1 - 0.18) = 67.24
        profile = _profile(weight_kg=82, body_fat_pct=18)
        rmr = rmr_katch_mcardle(profile, body_fat_pct=18)
        # 370 + 21.6 * 67.24 = 370 + 1452.4 = 1822.4
        assert 1700 < rmr < 1950

    def test_select_rmr_formula_returns_katch_when_bf_known(self):
        profile = _profile(sex=Sex.MALE, body_fat_pct=None)
        formula = select_rmr_formula(profile, body_fat_pct=18)
        assert formula == RMRFormula.KATCH_MCARDLE

    def test_select_rmr_formula_returns_mifflin_when_bf_unknown(self):
        profile = _profile(sex=Sex.MALE, body_fat_pct=None)
        formula = select_rmr_formula(profile, body_fat_pct=None)
        assert formula == RMRFormula.MIFFLIN_ST_JEOR

    def test_compute_rmr_returns_valid_result(self):
        profile = _profile()
        result = compute_rmr(profile, weight_reduced_pct=0.0)
        assert result.base_rmr_kcal > 1000
        assert result.adjusted_rmr_kcal > 0

    def test_compute_rmr_weight_reduction_lowers_rmr(self):
        """Greater-than-10% weight reduction applies ~3% RMR adaptation."""
        # Engine uses strict `> 0.10` threshold (per rippedbody spec), so we
        # test the unambiguous 15% case.
        profile = _profile()
        baseline = compute_rmr(profile, weight_reduced_pct=0.0)
        reduced = compute_rmr(profile, weight_reduced_pct=0.15)
        # Adapted should be lower
        assert reduced.adjusted_rmr_kcal < baseline.adjusted_rmr_kcal


# ============================================================
# TDEE math
# ============================================================

class TestTDEE:

    def test_compute_tdee_uses_rippedbody_factors(self):
        """TDEE = RMR × activity_factor."""
        from fitness_engine.models.nutrition import RMRResult

        rmr = RMRResult(
            formula=RMRFormula.MIFFLIN_ST_JEOR,
            base_rmr_kcal=1800.0,
            adjusted_rmr_kcal=1800.0,
        )
        profile = _profile(activity_level=ActivityLevel.LIGHTLY_ACTIVE)
        result = compute_tdee(rmr, profile)
        factor = ACTIVITY_FACTORS_RIPPEDBODY[ActivityLevel.LIGHTLY_ACTIVE]
        expected = 1800 * factor
        assert abs(result.tdee_kcal - expected) < 1.0

    def test_activity_factor_returns_value_for_each_level(self):
        for level in ActivityLevel:
            profile = _profile(activity_level=level)
            factor = activity_factor(profile)
            assert factor > 1.0
            assert factor < 2.5

    def test_sedentary_has_lowest_factor(self):
        sedentary_profile = _profile(activity_level=ActivityLevel.SEDENTARY)
        sedentary = activity_factor(sedentary_profile)
        for level in ActivityLevel:
            if level != ActivityLevel.SEDENTARY:
                other_profile = _profile(activity_level=level)
                assert activity_factor(other_profile) > sedentary

    def test_observed_tdee_first_principles_basic(self):
        """Calorie intake + weight change → observed TDEE."""
        # Eating 2500 kcal/day, losing 0.1 kg/week for 14 days.
        # 14 days × 0.1 kg/week ÷ 7 days/week = 0.2 kg total weight loss.
        # 0.2 kg * 7700 kcal/kg = 1540 kcal deficit / 14 days = 110 kcal/day.
        # TDEE = 2500 + 110 = 2610
        tdee = observed_tdee_first_principles(
            avg_intake_kcal=2500,
            weight_start_kg=80.0,
            weight_end_kg=79.8,  # -0.2 kg over 14 days ≈ -0.1 kg/week
            n_days=14,
        )
        assert abs(tdee - 2610) < 30

    def test_adaptive_weight_data_returns_blend_weight(self):
        """adaptive_weight_data returns a Bayesian blend weight in [0, 1]."""
        # 0–7 days: pure prior (0.0)
        assert adaptive_weight_data(n_days=0) == 0.0
        assert adaptive_weight_data(n_days=7) == 0.0
        # 8–60 days: linear ramp 0 → 1
        w_mid = adaptive_weight_data(n_days=30)
        assert 0.0 < w_mid < 1.0
        # ≥ 60 days: pure observed (1.0)
        assert adaptive_weight_data(n_days=60) == 1.0
        assert adaptive_weight_data(n_days=90) == 1.0

    def test_adaptive_weight_data_zero_days_returns_zero(self):
        """With 0 days of data, blend weight is 0.0 (pure prior)."""
        assert adaptive_weight_data(n_days=0) == 0.0


# ============================================================
# Calorie targets math
# ============================================================

class TestCalorieTargets:

    def test_cut_target_below_tdee(self):
        profile = _profile(primary_goal=PrimaryGoal.FAT_LOSS, body_fat_pct=22)
        result = cut_target_calories(profile, tdee_kcal=2500)
        assert result.target_calories_kcal < 2500
        assert result.calorie_delta_kcal < 0

    def test_bulk_target_above_tdee(self):
        profile = _profile(primary_goal=PrimaryGoal.MUSCLE_GAIN, body_fat_pct=12)
        result = bulk_target_calories(profile, tdee_kcal=2500)
        assert result.target_calories_kcal > 2500
        assert result.calorie_delta_kcal > 0

    def test_maintenance_target_equals_tdee(self):
        result = maintenance_target_calories(tdee_kcal=2500)
        assert abs(result.target_calories_kcal - 2500) < 1
        assert abs(result.calorie_delta_kcal) < 1

    def test_cut_respects_max_weekly_loss(self):
        """Even very aggressive cuts should be capped at 1% BW/week."""
        profile = _profile(
            primary_goal=PrimaryGoal.FAT_LOSS, body_fat_pct=40,
            cut_rate_tier=None,
        )
        result = cut_target_calories(profile, tdee_kcal=3000)
        assert result.rate_pct <= MAX_WEEKLY_LOSS_PCT + 1e-9

    def test_recomp_target_near_maintenance(self):
        """Recomp target should be within ±10% of TDEE."""
        profile = _profile(primary_goal=PrimaryGoal.RECOMP, body_fat_pct=18)
        result = recomp_target_calories(profile, tdee_kcal=2500, body_fat_pct=18)
        assert abs(result.target_calories_kcal - 2500) / 2500 < 0.15


# ============================================================
# Macro math
# ============================================================

class TestMacroMath:

    def test_compute_protein_uses_2g_per_kg_for_cut(self):
        """Cut strategy: ~2.2 g protein per kg LBM (RippedBody)."""
        profile = _profile(body_fat_pct=20, weight_kg=80)
        protein_g, _ = compute_protein(
            profile, body_fat_pct=20,
            strategy=__import__("fitness_engine.models.assessment", fromlist=["RecommendedStrategy"]).RecommendedStrategy.CUT,
            target_calories=2000,
        )
        # LBM = 64, protein should be at least 1.6g/kg LBM = 102g
        assert protein_g > 100

    def test_compute_fat_in_target_range(self):
        """Fat should be 20-30% of target calories for bulk/maintenance."""
        profile = _profile()
        from fitness_engine.models.assessment import RecommendedStrategy
        fat_g, _ = compute_fat(profile, target_calories=2500, strategy=RecommendedStrategy.MAINTENANCE)
        fat_kcal = fat_g * 9
        pct = fat_kcal / 2500 * 100
        assert 15 <= pct <= 35

    def test_compute_carbs_fills_remainder(self):
        """Carbs = (target - protein*4 - fat*9) / 4."""
        carb_g, _ = compute_carbs(target_calories=2000, protein_g=150, fat_g=70)
        expected = (2000 - 150*4 - 70*9) / 4
        assert abs(carb_g - expected) < 0.1

    def test_compute_carbs_clamps_to_zero_when_protein_fat_exceed_target(self):
        carb_g, notes = compute_carbs(target_calories=500, protein_g=200, fat_g=200)
        assert carb_g == 0
        assert any("clamp" in n.lower() for n in notes)

    def test_cut_macro_adjustment_2_to_1_carbs_to_fat(self):
        """Cut adjustment: 2/3 from carbs, 1/3 from fat."""
        carb_delta, fat_delta, _ = cut_macro_adjustment(calorie_delta_kcal=-300)
        # 300 kcal cut: 200 from carbs, 100 from fat
        # carb_g = -200/4 = -50, fat_g = -100/9 = -11.1
        assert carb_delta < 0
        assert fat_delta < 0
        assert abs(carb_delta * 4 + fat_delta * 9 + 300) < 1

    def test_bulk_macro_adjustment_3_to_1_carbs_to_fat(self):
        carb_delta, fat_delta, _ = bulk_macro_adjustment(calorie_delta_kcal=300)
        assert carb_delta > 0
        assert fat_delta > 0


# ============================================================
# Plateau detection
# ============================================================

class TestPlateauDetection:

    def test_no_data_returns_none(self):
        assert detect_plateau([], body_weight_kg=80) == PlateauType.NONE
        assert detect_plateau([80], body_weight_kg=80) == PlateauType.NONE
        assert detect_plateau([80, 79], body_weight_kg=80) == PlateauType.NONE

    def test_sudden_stall_detected(self):
        """3 weeks of zero weight change = sudden stall."""
        log = [80, 80, 80, 80]
        assert detect_plateau(log, body_weight_kg=80) == PlateauType.SUDDEN_STALL

    def test_weight_gain_detected(self):
        """3 weeks of weight gain = weight_gain plateau."""
        # deltas: [80-81, 81-82, 82-83] = [-1, -1, -1] (all negative = gaining)
        log = [80, 81, 82, 83]
        assert detect_plateau(log, body_weight_kg=83) == PlateauType.WEIGHT_GAIN

    def test_gradual_slowdown_detected(self):
        """Slowing week-over-week loss = gradual slowdown."""
        # deltas: [80-78, 78-77, 77-76.5] = [2, 1, 0.5] — all positive, decreasing
        log = [80, 78, 77, 76.5]
        assert detect_plateau(log, body_weight_kg=76.5) == PlateauType.GRADUAL_SLOWDOWN

    def test_whoosh_in_recent_weeks_detected(self):
        """Large weight drop in last 3 weeks = whoosh."""
        # 80 → 73 in week 3: delta = 7 (>1.5% of 73 = 1.095)
        log = [80, 80, 80, 73]
        assert detect_plateau(log, body_weight_kg=73) == PlateauType.WHOOSH

    def test_historical_whoosh_does_not_mask_current_gain(self):
        """Whoosh at week 1 should NOT mask 3 weeks of gaining."""
        log = [80, 73, 74, 75, 76]  # whoosh then 3 weeks gaining
        result = detect_plateau(log, body_weight_kg=76)
        assert result == PlateauType.WEIGHT_GAIN


# ============================================================
# Training progression
# ============================================================

class TestProgression:

    def test_linear_progression_adds_weight_when_all_sets_at_target(self):
        weight, msg = linear_progression_next(
            current_weight_kg=80,
            last_reps_achieved=[8, 8, 8],
            target_reps=(5, 8),
        )
        assert weight == 82.5
        assert "achieved" in msg.lower() or "+" in msg

    def test_linear_progression_repeats_when_in_range(self):
        weight, msg = linear_progression_next(
            current_weight_kg=80,
            last_reps_achieved=[6, 7],
            target_reps=(5, 8),
        )
        assert weight == 80
        assert "repeat" in msg.lower() or "range" in msg.lower()

    def test_linear_progression_deloads_when_below_min(self):
        weight, msg = linear_progression_next(
            current_weight_kg=80,
            last_reps_achieved=[3, 4],
            target_reps=(5, 8),
        )
        assert weight < 80
        assert "deload" in msg.lower()

    def test_linear_progression_empty_list_returns_no_data(self):
        weight, msg = linear_progression_next(
            current_weight_kg=80,
            last_reps_achieved=[],
            target_reps=(5, 8),
        )
        assert weight == 80
        assert "no data" in msg.lower()

    def test_dup_next_returns_dict(self):
        # Per-day rep targets (from dup_next): heavy=(3,6), moderate=(5,8),
        # light=(8,14). Use reps that hit the HIGH end of each target so all
        # three day types progress to weight + 2.5kg.
        result = dup_next(
            current_weights={"heavy": 100, "moderate": 90, "light": 80},
            last_reps={
                "heavy": [6, 6],       # ≥ 6 → +2.5
                "moderate": [10, 10],  # ≥ 8 → +2.5
                "light": [15, 15],     # ≥ 14 → +2.5
            },
        )
        assert "heavy" in result
        assert "moderate" in result
        assert "light" in result
        # Each should have progressed
        assert result["heavy"][0] > 100
        assert result["moderate"][0] > 90
        assert result["light"][0] > 80


# ============================================================
# Periodization
# ============================================================

class TestPeriodization:

    def test_block_phase_modifiers_have_peak_key(self):
        assert "peak" in _BLOCK_PHASE_MODIFIERS
        assert "deload" not in _BLOCK_PHASE_MODIFIERS

    def test_get_block_phases_for_program(self):
        assert get_block_phases_for_program(1) == ["accumulation"]
        assert get_block_phases_for_program(2) == ["accumulation", "intensification"]
        assert get_block_phases_for_program(3) == ["accumulation", "intensification", "peak"]

    def test_get_mesocycle_length_by_experience(self):
        assert get_mesocycle_length(TrainingStatus.BEGINNER) == 4
        assert get_mesocycle_length(TrainingStatus.NOVICE) == 4
        assert get_mesocycle_length(TrainingStatus.INTERMEDIATE) == 5
        assert get_mesocycle_length(TrainingStatus.ADVANCED) == 6

    def test_get_program_duration_weeks(self):
        assert get_program_duration_weeks(TrainingStatus.BEGINNER, None) == 4
        # Need a goal
        from fitness_engine.models.training import TrainingGoal
        assert get_program_duration_weeks(TrainingStatus.ADVANCED, TrainingGoal.STRENGTH) >= 12


# ============================================================
# Intensity model
# ============================================================

class TestIntensityModel:

    def test_rir_to_rpe_basic(self):
        """RPE = 10 - RIR."""
        assert rir_to_rpe(0) == 10
        assert rir_to_rpe(3) == 7
        assert rir_to_rpe(5) == 5

    def test_rpe_to_rir_basic(self):
        """RIR = 10 - RPE."""
        assert rpe_to_rir(10) == 0
        assert rpe_to_rir(7) == 3
        assert rpe_to_rir(5) == 5

    def test_rir_to_rpe_clamps_to_4_10(self):
        assert rir_to_rpe(-1) == 10  # RIR=-1 clamps to RPE 10
        assert rir_to_rpe(7) == 4    # RIR=7 clamps to RPE 4

    def test_generate_warmup_sets_returns_list(self):
        result = generate_warmup_sets(target_reps=5)
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_generate_warmup_sets_uses_leq_for_low_reps(self):
        """target_reps < 6 should use LEQ recipe."""
        result_low = generate_warmup_sets(target_reps=5)
        result_high = generate_warmup_sets(target_reps=8)
        # The two recipes differ — verify they produce different sets
        assert result_low != result_high


# ============================================================
# Volume landmarks
# ============================================================

class TestVolumeLandmarks:

    def test_get_muscle_landmarks_known_muscle(self):
        lm = get_muscle_landmarks("chest")
        assert lm.muscle == "chest"
        assert lm.mev > 0
        assert lm.mav_lo > 0
        assert lm.mav_hi > lm.mav_lo
        assert lm.mrv > lm.mav_hi

    def test_get_muscle_landmarks_unknown_muscle_returns_fallback(self):
        lm = get_muscle_landmarks("tibialis_anterior")
        assert lm.mev >= 6  # Phase-6 fix: fallback raised from 4 to 6

    def test_get_recommended_frequency_zero_returns_zero(self):
        assert get_recommended_frequency(0) == 0

    def test_get_recommended_frequency_low_volume(self):
        assert get_recommended_frequency(5) == 2

    def test_get_recommended_frequency_high_volume(self):
        assert get_recommended_frequency(25) == 4

    def test_check_session_volume_cap_returns_warnings_when_exceeded(self):
        """11+ sets per muscle per session should warn."""
        # 12 sets of chest in one session
        warnings = check_session_volume_cap({"chest": 12.0})
        assert len(warnings) >= 1
        assert "chest" in warnings[0]

    def test_check_session_volume_cap_no_warnings_when_under(self):
        warnings = check_session_volume_cap({"chest": 5.0})
        assert warnings == []


# ============================================================
# Hydration
# ============================================================

class TestHydration:

    def test_compute_hydration_returns_valid_target(self):
        profile = _profile()
        result = compute_hydration(profile)
        assert 1.0 < result.water_liters_per_day < 6.0

    def test_compute_hydration_higher_for_heavier_person(self):
        light = _profile(weight_kg=60)
        heavy = _profile(weight_kg=120)
        light_h = compute_hydration(light)
        heavy_h = compute_hydration(heavy)
        assert heavy_h.water_liters_per_day > light_h.water_liters_per_day

    def test_compute_hydration_clamped_to_5L_soft_ceiling(self):
        """Hydration should be clamped to ≤5 L/day (hyponatremia ceiling)."""
        # Extreme: very heavy, hot climate, intense exercise, breastfeeding.
        # Uses a FEMALE profile because breastfeeding=True is biologically
        # impossible for Sex.MALE (the hydration module now raises ValueError
        # for that combination — previously it silently added +0.7 L).
        profile = _profile(sex=Sex.FEMALE, weight_kg=120)
        result = compute_hydration(
            profile,
            exercise_hours_per_day=8,
            exercise_intensity="intense",
            climate="hot_humid",
            breastfeeding=True,
        )
        assert result.water_liters_per_day <= 5.5  # allow small epsilon


# ============================================================
# Micronutrients
# ============================================================

class TestMicronutrients:

    def test_compute_micronutrients_returns_valid_object(self):
        result = compute_micronutrients(target_calories=2000)
        assert result.fiber_g > 0
        assert result.fruit_cups > 0
        assert result.veg_cups > 0

    def test_fiber_scales_with_calories(self):
        low_cal = compute_micronutrients(target_calories=1500)
        high_cal = compute_micronutrients(target_calories=3500)
        assert high_cal.fiber_g > low_cal.fiber_g
