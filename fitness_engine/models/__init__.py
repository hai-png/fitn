"""
Models package — exports all data classes used by the engine.
"""
from .assessment import (
    ABSIRiskLevel,
    AssessmentResult,
    BMICategory,
    BodyComposition,
    BodyFatCategory,
    BodyFatMethod,
    HealthRiskAssessment,
    HealthRiskLevel,
    MuscularPotential,
    RecommendedStrategy,
)
from .meal import (
    DayPlan,
    FitnessPlan,
    FoodCategory,
    FoodItem,
    Meal,
    MealFood,
    MealPlan,
    MealType,
    Recipe,
    RecipeDietTag,
)
from .nutrition import (
    CalorieStrategy,
    CalorieTargets,
    HydrationTarget,
    MacroSplit,
    MicronutrientTargets,
    NutritionPlan,
    RMRFormula,
    RMRResult,
    TDEEResult,
)
from .preferences import PlanPreferences
from .profile import (
    ActivityLevel,
    BulkAggressiveness,
    Climate,
    CutRateTier,
    DietType,
    EquipmentAccess,
    ExerciseIntensity,
    PrimaryGoal,
    Sex,
    TrainingStatus,
    TrainingTimeOfDay,
    UserProfile,
)
from .training import (
    Exercise,
    ExerciseCategory,
    ExperienceLevel,
    Mesocycle,
    Microcycle,
    PlanType,
    ProgressionScheme,
    SplitType,
    TrainingGoal,
    TrainingPlan,
    Workout,
    WorkoutExercise,
)

__all__ = [
    # Profile
    "Sex", "ActivityLevel", "TrainingStatus", "PrimaryGoal", "EquipmentAccess",
    "DietType", "CutRateTier", "BulkAggressiveness", "UserProfile",
    "TrainingTimeOfDay", "ExerciseIntensity", "Climate",
    # Assessment
    "BodyFatMethod", "BodyFatCategory", "BMICategory", "HealthRiskLevel",
    "ABSIRiskLevel", "RecommendedStrategy", "BodyComposition",
    "HealthRiskAssessment", "MuscularPotential", "AssessmentResult",
    # Nutrition
    "CalorieStrategy", "RMRFormula", "RMRResult", "TDEEResult",
    "CalorieTargets", "MacroSplit", "HydrationTarget",
    "MicronutrientTargets", "NutritionPlan",
    # Training
    "PlanType", "TrainingGoal", "SplitType", "ProgressionScheme",
    "ExerciseCategory", "ExperienceLevel", "Exercise", "WorkoutExercise",
    "Workout", "Microcycle", "Mesocycle", "TrainingPlan",
    # Meal
    "MealType", "FoodCategory", "FoodItem", "MealFood", "Meal",
    "DayPlan", "MealPlan", "FitnessPlan", "Recipe", "RecipeDietTag",
    # Preferences (Phase-6 unified config)
    "PlanPreferences",
]
