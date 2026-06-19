"""
Models package — exports all data classes used by the engine.
"""
from .profile import (
    Sex, ActivityLevel, TrainingStatus, PrimaryGoal, EquipmentAccess,
    DietType, CutRateTier, BulkAggressiveness, UserProfile,
)
from .assessment import (
    BodyFatMethod, BodyFatCategory, BMICategory, HealthRiskLevel, ABSIRiskLevel,
    RecommendedStrategy, BodyComposition, HealthRiskAssessment,
    MuscularPotential, AssessmentResult,
)
from .nutrition import (
    CalorieStrategy, RMRFormula, RMRResult, TDEEResult, CalorieTargets,
    MacroSplit, HydrationTarget, MicronutrientTargets, NutritionPlan,
)
from .training import (
    SplitType, ProgressionScheme, ExerciseCategory, Exercise,
    WorkoutExercise, Workout, Microcycle, Mesocycle, TrainingPlan,
)
from .meal import (
    MealType, FoodCategory, FoodItem, MealFood, Meal, DayPlan,
    MealPlan, FitnessPlan,
)

__all__ = [
    # Profile
    "Sex", "ActivityLevel", "TrainingStatus", "PrimaryGoal", "EquipmentAccess",
    "DietType", "CutRateTier", "BulkAggressiveness", "UserProfile",
    # Assessment
    "BodyFatMethod", "BodyFatCategory", "BMICategory", "HealthRiskLevel",
    "ABSIRiskLevel", "RecommendedStrategy", "BodyComposition",
    "HealthRiskAssessment", "MuscularPotential", "AssessmentResult",
    # Nutrition
    "CalorieStrategy", "RMRFormula", "RMRResult", "TDEEResult",
    "CalorieTargets", "MacroSplit", "HydrationTarget",
    "MicronutrientTargets", "NutritionPlan",
    # Training
    "SplitType", "ProgressionScheme", "ExerciseCategory", "Exercise",
    "WorkoutExercise", "Workout", "Microcycle", "Mesocycle", "TrainingPlan",
    # Meal
    "MealType", "FoodCategory", "FoodItem", "MealFood", "Meal",
    "DayPlan", "MealPlan", "FitnessPlan",
]
