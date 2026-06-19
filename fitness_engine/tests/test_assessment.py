"""Unit tests for the assessment module."""
import math
import pytest

from fitness_engine.models.profile import (
    UserProfile, Sex, ActivityLevel, TrainingStatus, PrimaryGoal,
    EquipmentAccess, DietType,
)
from fitness_engine.assessment import (
    body_fat_navy, body_fat_bmi_jackson, body_fat_cun_bae,
    classify_bf, classify_bmi, compute_ffmi,
    compute_whr, classify_whr, compute_whtr, classify_whtr,
    compute_absi, classify_absi, ibw_devine,
    assess_profile,
)
from fitness_engine.assessment.decision import decide_strategy
from fitness_engine.assessment.muscular_potential import (
    berkhan_stage_max_weight_kg, FFMI_NATURAL_COMMON,
    BULK_RATE_BY_STATUS,
)


# === Test fixtures ===

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


# === Body composition tests ===

class TestBodyFatNavy:
    def test_male_navy_typical(self, male_profile):
        bf = body_fat_navy(male_profile)
        assert bf is not None
        # Should be in a reasonable range for this profile
        assert 5 < bf < 40

    def test_female_navy_typical(self, female_profile):
        bf = body_fat_navy(female_profile)
        assert bf is not None
        assert 10 < bf < 50

    def test_returns_none_when_missing_measurements(self):
        p = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=82,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        assert body_fat_navy(p) is None


class TestBodyFatBMIMethods:
    def test_jackson_male(self, male_profile):
        bf = body_fat_bmi_jackson(male_profile)
        assert 5 < bf < 40

    def test_cun_bae_male(self, male_profile):
        bf = body_fat_cun_bae(male_profile)
        assert 5 < bf < 40

    def test_cun_bae_female_higher_than_male_at_same_bmi(self):
        male = UserProfile(
            age=30, sex=Sex.MALE, height_cm=178, weight_kg=80,
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        female = UserProfile(
            age=30, sex=Sex.FEMALE, height_cm=165, weight_kg=68.7,  # ~same BMI
            activity_level=ActivityLevel.SEDENTARY,
            training_status=TrainingStatus.BEGINNER,
            primary_goal=PrimaryGoal.MAINTENANCE,
            training_days_per_week=3,
            equipment_access=EquipmentAccess.FULL_GYM,
            diet_type=DietType.OMNIVORE,
        )
        bf_m = body_fat_cun_bae(male)
        bf_f = body_fat_cun_bae(female)
        # Women should have higher BF% at same BMI+age due to sex_code term
        assert bf_f > bf_m


class TestBodyFatCategories:
    def test_athlete_range_male(self):
        assert classify_bf(8, Sex.MALE).value == "athlete"

    def test_fitness_range_male(self):
        assert classify_bf(15, Sex.MALE).value == "fitness"

    def test_obesity_threshold_male(self):
        assert classify_bf(25, Sex.MALE).value == "obesity"

    def test_athlete_range_female(self):
        assert classify_bf(15, Sex.FEMALE).value == "athlete"

    def test_obesity_threshold_female(self):
        assert classify_bf(32, Sex.FEMALE).value == "obesity"


class TestBMIClassification:
    def test_underweight(self):
        assert classify_bmi(17).value == "underweight"

    def test_normal(self):
        assert classify_bmi(22).value == "normal"

    def test_overweight(self):
        assert classify_bmi(27).value == "overweight"

    def test_obese(self):
        assert classify_bmi(32).value == "obese"


class TestFFMI:
    def test_ffmi_calculation(self):
        # 80 kg, 15% BF, 1.78m
        # FFM = 80 * 0.85 = 68 kg
        # FFMI = 68 / 1.78^2 = 68 / 3.1684 = ~21.46
        ffmi, norm = compute_ffmi(80, 15, 1.78)
        assert abs(ffmi - 21.46) < 0.5

    def test_normalized_ffmi_increases_for_shorter(self):
        # Shorter people get a bonus in normalized FFMI
        ffmi_tall, norm_tall = compute_ffmi(80, 15, 1.90)
        ffmi_short, norm_short = compute_ffmi(80, 15, 1.60)
        # At 1.90m (above 1.8 reference), normalized < raw
        assert norm_tall < ffmi_tall
        # At 1.60m (below 1.8 reference), normalized > raw
        assert norm_short > ffmi_short


# === Health risk tests ===

class TestWHR:
    def test_low_risk_male(self):
        whr = 0.80
        assert classify_whr(whr, Sex.MALE).value == "low"

    def test_high_risk_male(self):
        whr = 0.95
        assert classify_whr(whr, Sex.MALE).value == "high"

    def test_very_high_risk(self):
        whr = 1.10
        assert classify_whr(whr, Sex.MALE).value == "very_high"


class TestWHtR:
    def test_healthy_universal_boundary(self):
        # 0.5 is the universal boundary
        # Male at 0.45 should be low (healthy)
        assert classify_whtr(0.45, Sex.MALE).value == "low"
        # Male at 0.55 should be high
        assert classify_whtr(0.55, Sex.MALE).value == "high"


class TestABSI:
    def test_absi_computed(self):
        # Typical values
        absi = compute_absi(waist_cm=85, weight_kg=80, height_cm=178)
        # ABSI typically in 0.07-0.09 range
        assert 0.05 < absi < 0.12

    def test_absi_z_score_typical(self):
        from fitness_engine.assessment.health_risk import absi_z_score
        z = absi_z_score(0.082, 30, Sex.MALE)
        assert -3 < z < 3   # typical range


class TestIBW:
    def test_devine_male_5ft10(self):
        # 178 cm ≈ 70 in
        # IBW = 50 + 2.3 × (70 - 60) = 50 + 23 = 73 kg
        ibw = ibw_devine(178, Sex.MALE)
        assert abs(ibw - 73) < 0.5

    def test_devine_female_5ft5(self):
        # 165 cm ≈ 65 in
        # IBW = 45.5 + 2.3 × (65 - 60) = 45.5 + 11.5 = 57 kg
        ibw = ibw_devine(165, Sex.FEMALE)
        assert abs(ibw - 57) < 0.5


# === Decision tree tests ===

class TestDecisionTree:
    def test_obese_male_recommends_cut(self):
        strategy, _ = decide_strategy(
            profile=UserProfile(
                age=35, sex=Sex.MALE, height_cm=178, weight_kg=110,
                activity_level=ActivityLevel.SEDENTARY,
                training_status=TrainingStatus.INTERMEDIATE,
                primary_goal=PrimaryGoal.MAINTENANCE,  # auto-decide
                training_days_per_week=4,
                equipment_access=EquipmentAccess.FULL_GYM,
                diet_type=DietType.OMNIVORE,
            ),
            body_fat_pct=30,
            bmi=34.7,
        )
        assert strategy.value == "cut"

    def test_obese_beginner_recommends_habit_change(self):
        strategy, _ = decide_strategy(
            profile=UserProfile(
                age=35, sex=Sex.MALE, height_cm=178, weight_kg=110,
                activity_level=ActivityLevel.SEDENTARY,
                training_status=TrainingStatus.BEGINNER,
                primary_goal=PrimaryGoal.MAINTENANCE,
                training_days_per_week=3,
                equipment_access=EquipmentAccess.FULL_GYM,
                diet_type=DietType.OMNIVORE,
            ),
            body_fat_pct=32,
            bmi=34.7,
        )
        assert strategy.value == "habit_change_first"

    def test_explicit_fat_loss_respected(self, male_profile):
        strategy, _ = decide_strategy(
            male_profile, body_fat_pct=18, bmi=25.9
        )
        assert strategy.value == "cut"

    def test_prevent_cut_below_floor(self):
        strategy, _ = decide_strategy(
            profile=UserProfile(
                age=30, sex=Sex.MALE, height_cm=178, weight_kg=70,
                activity_level=ActivityLevel.LIGHTLY_ACTIVE,
                training_status=TrainingStatus.INTERMEDIATE,
                primary_goal=PrimaryGoal.FAT_LOSS,
                training_days_per_week=4,
                equipment_access=EquipmentAccess.FULL_GYM,
                diet_type=DietType.OMNIVORE,
            ),
            body_fat_pct=8,  # below cut floor
            bmi=22.1,
        )
        assert strategy.value == "maintenance"  # auto-promote to maintenance

    def test_prevent_bulk_above_ceiling(self):
        strategy, _ = decide_strategy(
            profile=UserProfile(
                age=30, sex=Sex.MALE, height_cm=178, weight_kg=85,
                activity_level=ActivityLevel.LIGHTLY_ACTIVE,
                training_status=TrainingStatus.INTERMEDIATE,
                primary_goal=PrimaryGoal.MUSCLE_GAIN,
                training_days_per_week=4,
                equipment_access=EquipmentAccess.FULL_GYM,
                diet_type=DietType.OMNIVORE,
            ),
            body_fat_pct=22,  # above bulk ceiling
            bmi=26.8,
        )
        assert strategy.value == "cut"  # auto-redirect to cut


# === Muscular potential tests ===

class TestMuscularPotential:
    def test_berkhan_model_178cm(self):
        # 178 - 100 = 78 kg
        assert abs(berkhan_stage_max_weight_kg(178) - 78) < 0.01

    def test_berkhan_model_183cm(self):
        assert abs(berkhan_stage_max_weight_kg(183) - 83) < 0.01

    def test_ffmi_ceiling_value(self):
        assert FFMI_NATURAL_COMMON == 25.0

    def test_bulk_rates_by_status(self):
        assert BULK_RATE_BY_STATUS[TrainingStatus.BEGINNER] == 0.020
        assert BULK_RATE_BY_STATUS[TrainingStatus.ADVANCED] == 0.005


# === Full assessment integration test ===

class TestFullAssessment:
    def test_assess_profile_returns_complete_result(self, male_profile):
        result = assess_profile(male_profile)
        assert result.body_composition is not None
        assert result.health_risk is not None
        assert result.muscular_potential is not None
        assert result.recommended_strategy is not None
        assert isinstance(result.summary, str)
        assert len(result.summary) > 50

    def test_assessment_to_dict_serializable(self, male_profile):
        result = assess_profile(male_profile)
        d = result.to_dict()
        # Should be JSON-serializable
        import json
        json_str = json.dumps(d, default=str)
        assert len(json_str) > 100
