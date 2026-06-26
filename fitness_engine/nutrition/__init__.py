"""Nutrition module — RMR, TDEE, adaptive TDEE, calories, macros, hydration, micros, adjustments."""
from .adjustments import (
    AdjustmentRecommendation,
    PlateauType,
    detect_plateau,
    recommend_bulk_adjustment,
    recommend_cut_adjustment,
)
from .calories import (
    BULK_RATE_BY_STATUS,
    BULK_WEEKLY_RATE_TIERS,
    CUT_RATE_TIERS,
    DEFAULT_CUT_RATE_PCT,
    DEFICIT_KCAL_PER_KG_PER_WEEK,
    DEFICIT_KCAL_PER_LB_PER_WEEK,
    KCAL_PER_KG_FAT,
    KCAL_PER_LB_FAT,
    KCAL_PER_LB_MUSCLE,
    MAX_WEEKLY_LOSS_PCT,
    MIN_CALORIES,
    REVERSE_DIET_RED_FLAG_WEEKLY_GAIN_PCT,
    REVERSE_DIET_WEEKLY_INCREMENT,
    SURPLUS_KCAL_PER_KG_PER_MONTH,
    SURPLUS_KCAL_PER_LB_PER_MONTH,
    SWEET_SPOT_CUT_RATE_PCT,
    bulk_target_calories,
    compute_calorie_targets,
    cut_target_calories,
    maintenance_target_calories,
    recomp_target_calories,
    reverse_diet_plan,
)
from .hydration import (
    BASE_ML_PER_KG,
    BREASTFEEDING_ADD_ML,
    CLIMATE_MULTIPLIER,
    EFSA_AI,
    NAM_AI,
    PREGNANCY_ADD_ML,
    SEX_ADD_ML,
    SWEAT_RATE_ML_PER_HR,
    compute_hydration,
)
from .macros import (
    FAT_ABSOLUTE_FLOOR_G,
    FAT_PCT_RANGES,
    FAT_PER_LB_FLOOR,
    KCAL_PER_GRAM,
    SATURATED_FAT_CEILING_PCT,
    bulk_macro_adjustment,
    compute_carbs,
    compute_fat,
    compute_macros,
    compute_protein,
    cut_macro_adjustment,
)
from .micronutrients import (
    FIBER_G_PER_1000_KCAL,
    FRUIT_VEG_TIERS,
    compute_micronutrients,
)
from .planner import build_nutrition_plan
from .rmr import (
    BF_PCT_MAX,
    BF_PCT_MIN,
    compute_rmr,
    rmr_cunningham,
    rmr_harris_benedict_original,
    rmr_harris_benedict_revised,
    rmr_katch_mcardle,
    rmr_mifflin_st_jeor,
    select_rmr_formula,
)
from .tdee import (
    ACTIVITY_FACTORS_HARRIS_BENEDICT,
    ACTIVITY_FACTORS_RIPPEDBODY,
    activity_factor,
    adaptive_tdee,
    adaptive_weight_data,
    compute_tdee,
    observed_tdee_first_principles,
    update_tdee_with_logs,
)

__all__ = [
    # RMR
    "rmr_mifflin_st_jeor", "rmr_harris_benedict_original",
    "rmr_harris_benedict_revised", "rmr_cunningham", "rmr_katch_mcardle",
    "select_rmr_formula", "compute_rmr",
    "BF_PCT_MIN", "BF_PCT_MAX",
    # TDEE
    "ACTIVITY_FACTORS_RIPPEDBODY", "ACTIVITY_FACTORS_HARRIS_BENEDICT",
    "activity_factor", "compute_tdee",
    "observed_tdee_first_principles", "adaptive_weight_data", "adaptive_tdee",
    "update_tdee_with_logs",
    # Calories
    "KCAL_PER_LB_FAT", "KCAL_PER_KG_FAT", "KCAL_PER_LB_MUSCLE",
    "SURPLUS_KCAL_PER_LB_PER_MONTH", "SURPLUS_KCAL_PER_KG_PER_MONTH",
    "DEFICIT_KCAL_PER_LB_PER_WEEK", "DEFICIT_KCAL_PER_KG_PER_WEEK",
    "MIN_CALORIES", "MAX_WEEKLY_LOSS_PCT",
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
