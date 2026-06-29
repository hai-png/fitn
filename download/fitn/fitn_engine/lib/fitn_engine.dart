/// Fitn Engine — public API.
///
/// Pure-Dart physiology-grounded fitness engine. Deterministic (same inputs →
/// byte-identical output). See spec §4.
///
/// Usage:
/// ```dart
/// import 'package:fitn_engine/fitn_engine.dart';
///
/// void main() async {
///   final data = await loadEngineData();
///   final engine = FitnEngine(data: data);
///   final result = engine.generatePlan(profile, prefs);
///   print(result.plan.summary);
/// }
/// ```
library;

// Models (public).
export 'src/models/enums.dart';
export 'src/models/profile.dart';
export 'src/models/preferences.dart';
export 'src/models/assessment.dart';
export 'src/models/nutrition.dart';
export 'src/models/training.dart';
export 'src/models/meal.dart';
export 'src/models/fitness_plan.dart';

// Errors + version.
export 'src/errors.dart';
export 'src/version.dart';

// Engine data.
export 'src/engine_data.dart';

// Assessment sub-engine (public for direct use).
export 'src/assessment/assessor.dart';
export 'src/assessment/body_composition.dart';
export 'src/assessment/health_risk.dart';
export 'src/assessment/muscular_potential.dart';
export 'src/assessment/decision.dart';
export 'src/assessment/thresholds.dart';
export 'src/assessment/constants.dart';
export 'src/assessment/categories.dart';

// Nutrition sub-engine.
export 'src/nutrition/planner.dart';
export 'src/nutrition/rmr.dart';
export 'src/nutrition/tdee.dart';
export 'src/nutrition/calories.dart';
export 'src/nutrition/macros.dart';
export 'src/nutrition/hydration.dart';
export 'src/nutrition/micronutrients.dart';
export 'src/nutrition/adjustments.dart';

// Training sub-engine.
export 'src/training/architect.dart';
export 'src/training/exercise_library.dart';
export 'src/training/exercise_selector.dart';
export 'src/training/exercise_categorization.dart';
export 'src/training/volume_landmarks.dart';
export 'src/training/intensity_model.dart';
export 'src/training/periodization.dart';
export 'src/training/split_designs.dart';

// Meal plan sub-engine.
export 'src/meal_plan/allocator.dart';
export 'src/meal_plan/recipe_loader.dart';
export 'src/meal_plan/recipe_scorer.dart';
export 'src/meal_plan/food_database.dart';
export 'src/meal_plan/allergen_constants.dart';
export 'src/meal_plan/meal_templates.dart';

import 'dart:io';

import 'src/models/enums.dart';
import 'src/models/profile.dart';
import 'src/models/preferences.dart';
import 'src/models/assessment.dart';
import 'src/models/fitness_plan.dart';
import 'src/errors.dart';
import 'src/version.dart';
import 'src/engine_data.dart';

import 'src/assessment/assessor.dart';
import 'src/nutrition/planner.dart';
import 'src/training/architect.dart';
import 'src/training/exercise_library.dart';
import 'src/training/split_designs.dart';
import 'src/meal_plan/allocator.dart';
import 'src/meal_plan/recipe_loader.dart';
import 'src/meal_plan/food_database.dart';

/// The Fitn engine. Stateless except for the [data] it holds.
///
/// Construct once at app startup; pass to every isolate that needs to generate
/// plans.
class FitnEngine {
  FitnEngine({required EngineData data}) : _data = data {
    _exerciseLibrary = ExerciseLibrary(data.exercises);
    _recipeLibrary = RecipeLibrary(data.recipes);
    _foodDatabase = FoodDatabase(
        data.foodDatabase.values.toList());
  }

  final EngineData _data;
  late final ExerciseLibrary _exerciseLibrary;
  late final RecipeLibrary _recipeLibrary;
  late final FoodDatabase _foodDatabase;

  /// Run the assessment pipeline. See §4.2.
  ///
  /// Never throws — partial assessments are returned with `isPartial == true`
  /// and errors captured in `errors`.
  AssessmentResult assessProfile(UserProfile profile) {
    return runAssessment(profile);
  }

  /// Propose a plan from a (profile, assessment, prefs) triple.
  ///
  /// Throws [PartialAssessmentError] if `assessment.isPartial == true`. The UI
  /// must check `assessment.isPartial` first and surface a "regenerate" CTA
  /// instead of attempting plan generation.
  FitnessPlan proposePlan(
    UserProfile profile,
    AssessmentResult assessment,
    PlanPreferences prefs,
  ) {
    if (assessment.isPartial) {
      throw PartialAssessmentError(assessment.errors);
    }

    // 1. Nutrition.
    final nutrition = buildNutritionPlan(
      profile: profile,
      assessment: assessment,
      prefs: prefs,
    );

    // 2. Training.
    final training = buildTrainingPlan(
      profile: profile,
      assessment: assessment,
      prefs: prefs,
      exerciseLibrary: _exerciseLibrary,
      splits: _data.splits,
      patterns: _data.movementPatterns,
    );

    // 3. Meal plan.
    final meal = buildMealPlan(
      profile: profile,
      assessment: assessment,
      nutrition: nutrition,
      prefs: prefs,
      recipeLibrary: _recipeLibrary,
      foodDb: _foodDatabase,
    );

    // 4. Summary.
    final summary = _buildPlanSummary(profile, assessment, nutrition, training,
        meal);

    return FitnessPlan(
      nutrition: nutrition,
      training: training,
      meal: meal,
      summary: summary,
      engineVersion: engineVersion,
    );
  }

  /// Convenience: assess + propose in one call.
  GeneratePlanResponse generatePlan(
    UserProfile profile,
    PlanPreferences prefs,
  ) {
    final assessment = assessProfile(profile);
    // Even if partial, we return the assessment so the UI can decide what to do.
    if (assessment.isPartial) {
      // Return a response with a null plan? The spec says proposePlan throws.
      // For convenience, we'll throw here too so callers can catch.
      throw PartialAssessmentError(assessment.errors);
    }
    final plan = proposePlan(profile, assessment, prefs);
    return GeneratePlanResponse(
      profile: profile,
      preferences: prefs,
      assessment: assessment,
      plan: plan,
    );
  }

  String _buildPlanSummary(
    UserProfile profile,
    AssessmentResult assessment,
    NutritionPlan nutrition,
    TrainingPlan training,
    MealPlan meal,
  ) {
    final lines = <String>[];
    lines.add('Fitn plan v$engineVersion');
    lines.add(
        '${profile.sex.display} ${profile.age}y · ${profile.trainingStatus.display} · goal: ${profile.primaryGoal.display}');
    lines.add(
        'Strategy: ${assessment.recommendedStrategy.display}');
    lines.add(
        'Calories: ${nutrition.calories.targetCaloriesKcal.toStringAsFixed(0)} kcal/day · ${nutrition.calories.rateLabel}');
    lines.add(
        'Macros: P ${nutrition.macros.proteinG.toStringAsFixed(0)}g · C ${nutrition.macros.carbG.toStringAsFixed(0)}g · F ${nutrition.macros.fatG.toStringAsFixed(0)}g');
    lines.add(
        'Hydration: ${nutrition.hydration.waterLitersPerDay.toStringAsFixed(1)} L/day');
    lines.add(
        'Training: ${training.splitType.display} · ${training.progression.display} · ${training.totalDurationWeeks}w');
    lines.add(
        'Meals: ${meal.mealFrequency}/day · 7-day rotation');
    return lines.join('\n');
  }
}

/// Engine data container.
class EngineData {
  EngineData({
    required this.exercises,
    required this.splits,
    required this.movementPatterns,
    required this.recipes,
    required this.foodDatabase,
  });

  final List<Exercise> exercises;
  final List<SplitDesign> splits;
  final Map<String, MovementPatternSpec> movementPatterns;
  final List<Recipe> recipes;
  final Map<String, FoodItem> foodDatabase;
}
