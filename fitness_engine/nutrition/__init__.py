"""Nutrition module — RMR, TDEE, adaptive TDEE, calories, macros, hydration, micros, adjustments."""
from .rmr import (
    rmr_mifflin_st_jeor, rmr_harris_benedict_original,
    rmr_harris_benedict_revised, rmr_cunningham,
    select_rmr_formula, compute_rmr,
)
from .tdee import (
    ACTIVITY_FACTORS_RIPPEDBODY, ACTIVITY_FACTORS_HARRIS_BENEDICT,
    activity_factor, compute_tdee,
    observed_tdee_first_principles, adaptive_weight_data, adaptive_tdee,
    update_tdee_with_logs,
)
from .calories import (
    KCAL_PER_LB_FAT, KCAL_PER_KG_FAT, KCAL_PER_LB_MUSCLE,
    SURPLUS_KCAL_PER_LB_PER_MONTH, SURPLUS_KCAL_PER_KG_PER_MONTH,
    DEFICIT_KCAL_PER_LB_PER_WEEK, DEFICIT_KCAL_PER_KG_PER_WEEK,
    MIN_CALORIES, MAX_WEEKLY_LOSS_LB, MAX_WEEKLY_LOSS_KG, MAX_WEEKLY_LOSS_PCT,
    CUT_RATE_TIERS, DEFAULT_CUT_RATE_PCT, SWEET_SPOT_CUT_RATE_PCT,
    BULK_RATE_BY_STATUS, BULK_WEEKLY_RATE_TIERS,
    REVERSE_DIET_WEEKLY_INCREMENT, REVERSE_DIET_RED_FLAG_WEEKLY_GAIN_PCT,
    cut_target_calories, bulk_target_calories,
    maintenance_target_calories, recomp_target_calories,
    reverse_diet_plan, compute_calorie_targets,
)
from .macros import (
    KCAL_PER_GRAM, FAT_PCT_RANGES,
    FAT_ABSOLUTE_FLOOR_G, FAT_PER_LB_FLOOR, SATURATED_FAT_CEILING_PCT,
    compute_protein, compute_fat, compute_carbs,
    compute_macros, cut_macro_adjustment, bulk_macro_adjustment,
)
from .hydration import (
    BASE_ML_PER_KG, SEX_ADD_ML, SWEAT_RATE_ML_PER_HR,
    CLIMATE_MULTIPLIER, PREGNANCY_ADD_ML, BREASTFEEDING_ADD_ML,
    EFSA_AI, NAM_AI,
    compute_hydration,
)
from .micronutrients import (
    FIBER_G_PER_1000_KCAL, FRUIT_VEG_TIERS,
    compute_micronutrients,
)
from .adjustments import (
    PlateauType, AdjustmentRecommendation,
    detect_plateau, recommend_cut_adjustment, recommend_bulk_adjustment,
)
from .planner import build_nutrition_plan

__all__ = [
    # RMR
    "rmr_mifflin_st_jeor", "rmr_harris_benedict_original",
    "rmr_harris_benedict_revised", "rmr_cunningham",
    "select_rmr_formula", "compute_rmr",
    # TDEE
    "ACTIVITY_FACTORS_RIPPEDBODY", "ACTIVITY_FACTORS_HARRIS_BENEDICT",
    "activity_factor", "compute_tdee",
    "observed_tdee_first_principles", "adaptive_weight_data", "adaptive_tdee",
    "update_tdee_with_logs",
    # Calories
    "KCAL_PER_LB_FAT", "KCAL_PER_KG_FAT", "KCAL_PER_LB_MUSCLE",
    "SURPLUS_KCAL_PER_LB_PER_MONTH", "SURPLUS_KCAL_PER_KG_PER_MONTH",
    "DEFICIT_KCAL_PER_LB_PER_WEEK", "DEFICIT_KCAL_PER_KG_PER_WEEK",
    "MIN_CALORIES", "MAX_WEEKLY_LOSS_LB", "MAX_WEEKLY_LOSS_KG", "MAX_WEEKLY_LOSS_PCT",
    "CUT_RATE_TIERS", "DEFAULT_CUT_RATE_PCT", "SWEET_SPOT_CUT_RATE_PCT",
    "BULK_RATE_BY_STATUS", "BULK_WEEKLY_RATE_TIERS",
    "REVERSE_DIET_WEEKLY_INCREMENT", "REVERSE_DIET_RED_FLAG_WEEKLY_GAIN_PCT",
    "cut_target_calories", "bulk_target_calories",
    "maintenance_target_calories", "recomp_target_calories",
    "reverse_diet_plan", "compute_calorie_targets",
    # Macros
    "KCAL_PER_GRAM", "FAT_PCT_RANGES",
    "FAT_ABSOLUTE_FLOOR_G", "FAT_PER_LB_FLOOR", "SATURATED_FAT_CEILING_PCT",
    "compute_protein", "compute_fat", "compute_carbs",
    "compute_macros", "cut_macro_adjustment", "bulk_macro_adjustment",
    # Hydration
    "BASE_ML_PER_KG", "SEX_ADD_ML", "SWEAT_RATE_ML_PER_HR",
    "CLIMATE_MULTIPLIER", "PREGNANCY_ADD_ML", "BREASTFEEDING_ADD_ML",
    "EFSA_AI", "NAM_AI",
    "compute_hydration",
    # Micros
    "FIBER_G_PER_1000_KCAL", "FRUIT_VEG_TIERS",
    "compute_micronutrients",
    # Adjustments
    "PlateauType", "AdjustmentRecommendation",
    "detect_plateau", "recommend_cut_adjustment", "recommend_bulk_adjustment",
    # Planner
    "build_nutrition_plan",
]
