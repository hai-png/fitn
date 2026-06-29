import 'package:fitn_engine/src/models/meal.dart';

/// Pre/post-workout recipe selection. Spec §4.5 + §9.4.
///
/// 4 diets × 2 meal types (pre, post) × 2 kcal bins = 16 entries in
/// `pre_post_workout_recipes.json`.
///
/// Pre: <200 kcal, 200-400 kcal. Post: <300 kcal, 300-500 kcal.
class PrePostWorkoutSelector {
  final List<Recipe> prePostRecipes;

  PrePostWorkoutSelector(this.prePostRecipes);

  /// Pick a pre-workout recipe for the given slot kcal target.
  Recipe? pickPreWorkout({
    required double targetKcal,
    required String dietTag,
  }) {
    return _pick(
      targetKcal: targetKcal,
      dietTag: dietTag,
      mealType: 'pre_workout',
      lowBin: 200,
      highBin: 400,
    );
  }

  /// Pick a post-workout recipe for the given slot kcal target.
  Recipe? pickPostWorkout({
    required double targetKcal,
    required String dietTag,
  }) {
    return _pick(
      targetKcal: targetKcal,
      dietTag: dietTag,
      mealType: 'post_workout',
      lowBin: 300,
      highBin: 500,
    );
  }

  Recipe? _pick({
    required double targetKcal,
    required String dietTag,
    required String mealType,
    required double lowBin,
    required double highBin,
  }) {
    if (prePostRecipes.isEmpty) return null;
    final isVegan = dietTag.toUpperCase().startsWith('VEGAN');

    // Filter by meal type + diet tag.
    final candidates = prePostRecipes.where((r) {
      if (!r.mealTypes.any((m) => m.name == mealType)) return false;
      if (isVegan && !r.dietTypes.any((d) =>
          d.name.toUpperCase() == 'VEGAN' ||
          d.name.toUpperCase() == 'VEGAN_ETHIOPIAN')) {
        return false;
      }
      return true;
    }).toList();
    if (candidates.isEmpty) return null;

    // Pick the closest by kcal.
    candidates.sort((a, b) {
      final da = (a.nutritionPerServing.kcal - targetKcal).abs();
      final db = (b.nutritionPerServing.kcal - targetKcal).abs();
      return da.compareTo(db);
    });
    return candidates.first;
  }
}
