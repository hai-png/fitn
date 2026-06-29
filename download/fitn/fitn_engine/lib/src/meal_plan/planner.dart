import 'package:fitn_engine/src/meal_plan/allocator.dart';
import 'package:fitn_engine/src/meal_plan/food_database.dart';
import 'package:fitn_engine/src/meal_plan/profile_requirements.dart';
import 'package:fitn_engine/src/meal_plan/recipe_loader.dart';
import 'package:fitn_engine/src/models/assessment.dart';
import 'package:fitn_engine/src/models/meal.dart';
import 'package:fitn_engine/src/models/nutrition.dart';
import 'package:fitn_engine/src/models/profile.dart';
import 'package:fitn_engine/src/utils/round.dart';

/// Top-level meal plan orchestrator. Spec §4.5.
MealPlan buildMealPlan({
  required UserProfile profile,
  required AssessmentResult assessment,
  required NutritionPlan nutrition,
  required RecipeLibrary library,
  required FoodDatabase foodDatabase,
  required int mealFrequency,
  required String cuisinePreference,
  required List<String> allergensToAvoid,
  required List<String> excludedIngredients,
  required bool includePrePostWorkout,
}) {
  final notes = <String>[];

  final allocator = Allocator(
    library: library,
    foodDatabase: foodDatabase,
    includePrePostWorkout: includePrePostWorkout,
  );

  final days = allocator.buildWeek(
    profile: profile,
    nutrition: nutrition,
    cuisinePreference: cuisinePreference,
    allergensToAvoid: allergensToAvoid,
    excludedIngredients: excludedIngredients,
  );

  // Compute macro allocation (fraction of daily kcal per meal type).
  final macroAllocation = <String, double>{};
  final cuisineMix = <String, int>{};
  var totalKcal = 0.0;
  var totalProtein = 0.0;
  var totalCarb = 0.0;
  var totalFat = 0.0;
  var totalFiber = 0.0;
  var uniqueRecipes = <String>{};
  var curatedUsed = 0;
  var uncuratedUsed = 0;
  var rawFallback = 0;
  var weeklyKcalMatchSum = 0.0;
  var weeklyProteinMatchSum = 0.0;
  var dayCount = 0;

  for (final day in days) {
    dayCount++;
    totalKcal += day.totalKcal;
    totalProtein += day.totalProteinG;
    totalCarb += day.totalCarbG;
    totalFat += day.totalFatG;
    totalFiber += day.totalFiberG;
    for (final meal in day.meals) {
      if (meal.recipe != null) {
        uniqueRecipes.add(meal.recipe!.id);
        if (meal.recipe!.isCurated) {
          curatedUsed++;
        } else {
          uncuratedUsed++;
        }
        if (meal.cuisine != null && meal.cuisine!.isNotEmpty) {
          cuisineMix[meal.cuisine!] = (cuisineMix[meal.cuisine!] ?? 0) + 1;
        }
        // (Note: Meal has no cuisine field; track via recipe.cuisine below.)
      } else {
        rawFallback++;
      }
      if (meal.targetKcal != null && meal.targetKcal! > 0) {
        weeklyKcalMatchSum += 1 -
            ((meal.actualKcal - meal.targetKcal!).abs() / meal.targetKcal!);
      }
      if (meal.targetProteinG != null && meal.targetProteinG! > 0) {
        weeklyProteinMatchSum += 1 -
            ((meal.actualProteinG - meal.targetProteinG!).abs() /
                meal.targetProteinG!);
      }
    }
  }

  // Track cuisine from recipe IDs (look up in library).
  for (final r in library.recipes) {
    if (uniqueRecipes.contains(r.id)) {
      cuisineMix[r.cuisine] = (cuisineMix[r.cuisine] ?? 0) + 1;
    }
  }

  final avgKcalMatch = dayCount > 0 ? weeklyKcalMatchSum / dayCount : 0.0;
  final avgProteinMatch = dayCount > 0 ? weeklyProteinMatchSum / dayCount : 0.0;
  // Trim cuisine mix (recipe + meal duplicates).
  final trimmedCuisine = <String, int>{};
  for (final entry in cuisineMix.entries) {
    if (entry.key.isEmpty) continue;
    trimmedCuisine[entry.key] = entry.value > 7 ? 7 : entry.value;
  }

  final macroAllocationTotal = totalKcal;
  if (macroAllocationTotal > 0) {
    macroAllocation['protein_pct'] = roundBankers(totalProtein * 4 / macroAllocationTotal, 4);
    macroAllocation['carb_pct'] = roundBankers(totalCarb * 4 / macroAllocationTotal, 4);
    macroAllocation['fat_pct'] = roundBankers(totalFat * 9 / macroAllocationTotal, 4);
  }

  final trainingDays = trainingDaysFor(profile.trainingDaysPerWeek);

  final sourceSummary = RecipeSourceSummary(
    curatedUsed: curatedUsed,
    uncuratedUsed: uncuratedUsed,
    fallbackToRawFoods: rawFallback,
    uniqueRecipesUsed: uniqueRecipes.length,
    databaseTotal: library.recipes.length,
    databaseCurated: library.curatedCount,
    databaseUncurated: library.uncuratedCount,
    weeklyAvgKcalMatchPct: roundBankers(avgKcalMatch * 100, 4),
    weeklyAvgProteinMatchPct: roundBankers(avgProteinMatch * 100, 4),
    weeklyKcalMatchPct: roundBankers(avgKcalMatch * 100, 4),
    weeklyProteinMatchPct: roundBankers(avgProteinMatch * 100, 4),
    trainingDays: trainingDays,
    includePrePostWorkout: includePrePostWorkout,
  );

  if (rawFallback > 0) {
    notes.add('$rawFallback meals had no matching recipe — raw foods only.');
  }
  notes.add('Unique recipes used: ${uniqueRecipes.length}.');
  notes.add('Weekly kcal match: ${(avgKcalMatch * 100).toStringAsFixed(1)}%.');
  notes.add('Weekly protein match: ${(avgProteinMatch * 100).toStringAsFixed(1)}%.');

  return MealPlan(
    days: days,
    mealFrequency: mealFrequency,
    macroAllocation: macroAllocation,
    cuisineMix: trimmedCuisine,
    recipeSourceSummary: sourceSummary,
    notes: notes,
  );
}

// Hack: extend Meal with cuisine getter for allocator stats.
// Since we don't have one in the model, we compute cuisine by lookup.
extension _MealCuisineX on Meal {
  String? get cuisine => recipe?.cuisine;
}
