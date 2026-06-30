/// Meal plan allocator + planner. See spec §4.5.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/preferences.dart';
import '../models/nutrition.dart';
import '../models/meal.dart';
import '../models/assessment.dart';
import '../utils/round.dart';
import 'allergen_constants.dart';
import 'food_database.dart';
import 'recipe_loader.dart';
import 'recipe_scorer.dart';
import 'meal_templates.dart';

/// Build the full 7-day meal plan.
MealPlan buildMealPlan({
  required UserProfile profile,
  required AssessmentResult assessment,
  required NutritionPlan nutrition,
  required PlanPreferences prefs,
  required RecipeLibrary recipeLibrary,
  required FoodDatabase foodDb,
}) {
  // Compute slot targets from daily macros × meal allocation.
  final allocation = mealAllocationForFrequency(prefs.mealFrequency);
  final dailyKcal = nutrition.calories.targetCaloriesKcal;
  final dailyProteinG = nutrition.macros.proteinG;
  final dailyCarbG = nutrition.macros.carbG;
  final dailyFatG = nutrition.macros.fatG;
  final dailyFiberG = nutrition.micronutrients.fiberG;

  final trainingDays = trainingDaysFor(profile.trainingDaysPerWeek);
  final recentRecipeIds = <String>{};
  final weekRecipeIds = <String>{};

  final days = <DayPlan>[];
  final cuisineMix = <String, int>{};

  for (var dayNum = 1; dayNum <= 7; dayNum++) {
    final isTrainingDay = trainingDays.contains(dayNum);
    final dayName = _dayName(dayNum);
    final meals = <Meal>[];

    for (final slot in allocation) {
      final target = SlotTarget(
        mealType: slot.mealType,
        targetKcal: round1(dailyKcal * slot.fraction),
        targetProteinG: round1(dailyProteinG * slot.fraction),
        targetCarbG: round1(dailyCarbG * slot.fraction),
        targetFatG: round1(dailyFatG * slot.fraction),
        targetFiberG: round1(dailyFiberG * slot.fraction),
      );

      final meal = _allocateMeal(
        dayNumber: dayNum,
        target: target,
        diet: profile.dietType,
        allergens: prefs.allergensToAvoid ?? const [],
        excluded: prefs.excludedIngredients,
        cuisine: prefs.cuisinePreference,
        recipeLibrary: recipeLibrary,
        foodDb: foodDb,
        recentRecipeIds: recentRecipeIds,
        weekRecipeIds: weekRecipeIds,
        isMainMeal: slot.mealType == MealType.breakfast ||
            slot.mealType == MealType.lunch ||
            slot.mealType == MealType.dinner,
      );
      meals.add(meal);

      // Track recipe usage for variety scoring.
      if (meal.recipe != null) {
        recentRecipeIds.add(meal.recipe!.id);
        weekRecipeIds.add(meal.recipe!.id);
        cuisineMix[meal.recipe!.cuisine] =
            (cuisineMix[meal.recipe!.cuisine] ?? 0) + 1;
      }
    }

    // Roll recentRecipeIds window (keep last 3 days = ~12 meals).
    if (recentRecipeIds.length > 12) {
      recentRecipeIds.remove(recentRecipeIds.first);
    }

    final totalKcal =
        meals.fold(0.0, (s, m) => s + m.actualKcal);
    final totalProteinG =
        meals.fold(0.0, (s, m) => s + m.actualProteinG);
    final totalCarbG =
        meals.fold(0.0, (s, m) => s + m.actualCarbG);
    final totalFatG =
        meals.fold(0.0, (s, m) => s + m.actualFatG);
    final totalFiberG =
        meals.fold(0.0, (s, m) => s + m.actualFiberG);

    days.add(DayPlan(
      dayNumber: dayNum,
      dayName: dayName,
      meals: meals,
      isTrainingDay: isTrainingDay,
      totalKcal: round1(totalKcal),
      totalProteinG: round1(totalProteinG),
      totalCarbG: round1(totalCarbG),
      totalFatG: round1(totalFatG),
      totalFiberG: round1(totalFiberG),
    ));
  }

  final macroAllocation = {
    for (final slot in allocation)
      slot.mealType.toJson(): slot.fraction,
  };

  final recipeSourceSummary = RecipeSourceSummary(
    curatedUsed: days
        .expand((d) => d.meals)
        .where((m) => m.recipe?.isCurated ?? false)
        .toSet()
        .length,
    uncuratedUsed: days
        .expand((d) => d.meals)
        .where((m) => m.recipe != null && !(m.recipe!.isCurated))
        .toSet()
        .length,
    fallbackToRawFoods: 0,
    uniqueRecipesUsed: days
        .expand((d) => d.meals)
        .where((m) => m.recipe != null)
        .map((m) => m.recipe!.id)
        .toSet()
        .length,
    databaseTotal: recipeLibrary.count,
    databaseCurated: recipeLibrary.curatedCount,
    databaseUncurated: recipeLibrary.uncuratedCount,
    trainingDays: trainingDays,
    includePrePostWorkout: prefs.includePrePostWorkout,
  );

  return MealPlan(
    days: days,
    mealFrequency: prefs.mealFrequency,
    macroAllocation: macroAllocation,
    cuisineMix: cuisineMix,
    recipeSourceSummary: recipeSourceSummary,
    notes: [
      'Meal frequency: ${prefs.mealFrequency}',
      'Training days: ${trainingDays.join(', ')}',
      'Pre/post workout: ${prefs.includePrePostWorkout ? "on" : "off"}',
      'Cuisine: ${prefs.cuisinePreference ?? 'any'}',
    ],
  );
}

Meal _allocateMeal({
  required int dayNumber,
  required SlotTarget target,
  required DietType diet,
  required List<String> allergens,
  required List<String>? excluded,
  required String? cuisine,
  required RecipeLibrary recipeLibrary,
  required FoodDatabase foodDb,
  required Set<String> recentRecipeIds,
  required Set<String> weekRecipeIds,
  required bool isMainMeal,
}) {
  // Score all compatible recipes for this slot.
  final compatible = recipeLibrary.compatibleWith(diet);
  var scored = <MapEntry<Recipe, ScoreBreakdown>>[];
  for (final r in compatible) {
    if (!r.mealTypes.contains(target.mealType)) continue;
    final score = scoreRecipeForSlot(
      recipe: r,
      target: target,
      diet: diet,
      allergensToAvoid: allergens,
      excludedIngredients: excluded,
      cuisinePreference: cuisine,
      recentRecipeIds: recentRecipeIds,
      weekRecipeIds: weekRecipeIds,
    );
    if (score != null) {
      scored.add(MapEntry(r, score));
    }
  }

  // Pick top scorer.
  scored.sort((a, b) => b.value.total.compareTo(a.value.total));
  final Recipe? selected = scored.isEmpty ? null : scored.first.key;
  final String selectionReason = scored.isEmpty
      ? 'No recipe matched (falling back to raw foods).'
      : 'Score ${scored.first.value.total.toStringAsFixed(1)} (${scored.first.value.components.entries.map((e) => '${e.key}=${e.value.toStringAsFixed(0)}').take(3).join(', ')})';

  if (selected == null) {
    // Fallback: empty meal with zeros.
    return Meal(
      mealType: target.mealType,
      name: mealNameFor(dayNumber, target.mealType),
      foods: const [],
      recipe: null,
      scaleFactor: 1.0,
      scaledNutrition: const {},
      targetKcal: target.targetKcal,
      targetProteinG: target.targetProteinG,
      targetCarbG: target.targetCarbG,
      targetFatG: target.targetFatG,
      actualKcal: 0,
      actualProteinG: 0,
      actualCarbG: 0,
      actualFatG: 0,
      selectionReason: selectionReason,
      notes: const ['No recipe matched.'],
    );
  }

  // Scale the recipe.
  final scaled = scaleRecipeForSlot(
      recipe: selected, targetKcal: target.targetKcal);

  // Compute gaps + add fillers.
  final proteinGap = target.targetProteinG - scaled.scaledNutrition['protein_g']!;
  final carbGap = target.targetCarbG - scaled.scaledNutrition['carb_g']!;
  final fatGap = target.targetFatG - scaled.scaledNutrition['fat_g']!;
  final fiberGap = target.targetFiberG - scaled.scaledNutrition['fiber_g']!;

  final fillers = computeFillers(
    kcalGap: target.targetKcal - scaled.scaledNutrition['kcal']!,
    proteinGap: proteinGap,
    carbGap: carbGap,
    fatGap: fatGap,
    fiberGap: fiberGap,
    foodDb: foodDb,
    diet: diet,
    allergens: allergens,
    isMainMeal: isMainMeal,
  );

  final actualKcal =
      scaled.scaledNutrition['kcal']! + fillers.totalKcal;
  final actualProteinG =
      scaled.scaledNutrition['protein_g']! + fillers.totalProteinG;
  final actualCarbG =
      scaled.scaledNutrition['carb_g']! + fillers.totalCarbG;
  final actualFatG =
      scaled.scaledNutrition['fat_g']! + fillers.totalFatG;

  return Meal(
    mealType: target.mealType,
    name: selected.name,
    foods: fillers.foods,
    recipe: selected,
    scaleFactor: scaled.scaleFactor,
    scaledNutrition: scaled.scaledNutrition,
    targetKcal: target.targetKcal,
    targetProteinG: target.targetProteinG,
    targetCarbG: target.targetCarbG,
    targetFatG: target.targetFatG,
    actualKcal: round1(actualKcal),
    actualProteinG: round1(actualProteinG),
    actualCarbG: round1(actualCarbG),
    actualFatG: round1(actualFatG),
    selectionReason: selectionReason,
    notes: const [],
  );
}

String _dayName(int n) {
  return switch (n) {
    1 => 'Monday',
    2 => 'Tuesday',
    3 => 'Wednesday',
    4 => 'Thursday',
    5 => 'Friday',
    6 => 'Saturday',
    7 => 'Sunday',
    _ => 'Day $n',
  };
}
