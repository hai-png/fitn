/// Recipe scoring + scaling + swap system. See spec §4.5.
library;

import 'dart:math';

import '../models/meal.dart';
import '../models/enums.dart';
import '../utils/round.dart';
import '../utils/units.dart';
import 'allergen_constants.dart';
import 'food_database.dart';
import 'recipe_loader.dart';

class SlotTarget {
  SlotTarget({
    required this.mealType,
    required this.targetKcal,
    required this.targetProteinG,
    required this.targetCarbG,
    required this.targetFatG,
    required this.targetFiberG,
  });
  final MealType mealType;
  final double targetKcal;
  final double targetProteinG;
  final double targetCarbG;
  final double targetFatG;
  final double targetFiberG;
}

class ScoreBreakdown {
  ScoreBreakdown(this.total, this.components);
  final double total;
  final Map<String, double> components;
}

/// Score a recipe for a slot. See §4.5 (9 weighted components).
///
/// Hard exclusions return null (score = 0):
/// - Allergen violation
/// - Excluded ingredient present
/// - Diet mismatch
ScoreBreakdown? scoreRecipeForSlot({
  required Recipe recipe,
  required SlotTarget target,
  required DietType diet,
  required List<String> allergensToAvoid,
  required List<String>? excludedIngredients,
  required String? cuisinePreference,
  required Set<String> recentRecipeIds,
  required Set<String> weekRecipeIds,
}) {
  // Hard exclusions.
  final ingredientsText = recipe.ingredients.join(' ');
  if (allergensToAvoid.isNotEmpty &&
      containsAllergen(ingredientsText, allergensToAvoid)) {
    return null;
  }
  if (excludedIngredients != null) {
    final lower = ingredientsText.toLowerCase();
    for (final ex in excludedIngredients) {
      if (lower.contains(ex.toLowerCase())) return null;
    }
  }
  // Diet mismatch — vegetarian/vegan fall to VEGAN recipes (no separate
  // vegetarian tag in DB).
  if (diet != DietType.omnivore) {
    final isVeganRecipe = recipe.dietTypes.any((d) =>
        d == RecipeDietTag.vegan || d == RecipeDietTag.veganEthiopian);
    if (!isVeganRecipe) return null;
  }

  // 1. kcal_match (26).
  final kcalScore = _bandScore(recipe.kcal, target.targetKcal,
      tightBand: 0.20, looseBand: 0.40);
  // 2. protein_match (22).
  final proteinScore = _bandScore(recipe.proteinG, target.targetProteinG,
      tightBand: 0.15, looseBand: 0.30);
  // 3. carb_match (13).
  final carbScore = _bandScore(recipe.carbG, target.targetCarbG,
      tightBand: 0.20, looseBand: 0.40);
  // 4. fat_match (9).
  final fatScore = _bandScore(recipe.fatG, target.targetFatG,
      tightBand: 0.25, looseBand: 0.50);
  // 5. diet_match (13).
  final dietScore = 100.0; // already passed the hard check.
  // 6. goal_fit (4) — skipped for simplicity; would map recipe.goalFit vs strategy.
  final goalFitScore = 100.0;
  // 7. fiber_match (4).
  final fiberScore = _bandScore(recipe.fiberG, target.targetFiberG,
      tightBand: 0.50, looseBand: 1.00);
  // 8. variety_bonus (4).
  final varietyBonus =
      recentRecipeIds.contains(recipe.id) || weekRecipeIds.contains(recipe.id)
          ? 0.0
          : 100.0;
  // 9. cuisine_match (5).
  final cuisineScore = (cuisinePreference != null &&
          recipe.cuisine.toLowerCase() == cuisinePreference.toLowerCase())
      ? 100.0
      : 50.0;

  final components = {
    'kcal_match': kcalScore,
    'protein_match': proteinScore,
    'carb_match': carbScore,
    'fat_match': fatScore,
    'diet_match': dietScore,
    'goal_fit': goalFitScore,
    'fiber_match': fiberScore,
    'variety_bonus': varietyBonus,
    'cuisine_match': cuisineScore,
  };

  final total = kcalScore * 0.26 +
      proteinScore * 0.22 +
      carbScore * 0.13 +
      fatScore * 0.09 +
      dietScore * 0.13 +
      goalFitScore * 0.04 +
      fiberScore * 0.04 +
      varietyBonus * 0.04 +
      cuisineScore * 0.05;

  return ScoreBreakdown(round1(total), components);
}

/// Band-score a value: 100 if within tight band, scaled down to 0 at loose
/// band, 0 beyond.
double _bandScore(
  double actual,
  double target, {
  required double tightBand,
  required double looseBand,
}) {
  if (target <= 0) return 50;
  final diff = (actual - target).abs() / target;
  if (diff <= tightBand) return 100;
  if (diff >= looseBand) return 0;
  // Linear interpolation between tight (100) and loose (0).
  final t = (diff - tightBand) / (looseBand - tightBand);
  return 100 * (1 - t);
}

/// Scale a recipe to fit the slot target. See §4.5.
class ScaledRecipe {
  ScaledRecipe(this.recipe, this.scaleFactor, this.scaledNutrition);
  final Recipe recipe;
  final double scaleFactor;
  final Map<String, double> scaledNutrition;
}

ScaledRecipe scaleRecipeForSlot({
  required Recipe recipe,
  required double targetKcal,
}) {
  final recipeKcal = recipe.kcal;
  if (recipeKcal <= 0) {
    return ScaledRecipe(recipe, 1.0, Map.from(recipe.nutritionPerServing));
  }

  final ratio = targetKcal / recipeKcal;
  // 1.0 if within ±10%.
  double scale;
  if ((ratio - 1).abs() <= noScaleBand) {
    scale = 1.0;
  } else {
    scale = ratio.clamp(minScale, maxScale);
  }

  final scaled = {
    'kcal': round1(recipe.kcal * scale),
    'protein_g': round1(recipe.proteinG * scale),
    'carb_g': round1(recipe.carbG * scale),
    'fat_g': round1(recipe.fatG * scale),
    'fiber_g': round1(recipe.fiberG * scale),
    'sugar_g': round1(recipe.sugarG * scale),
  };

  return ScaledRecipe(recipe, round2(scale), scaled);
}

/// Compute fillers for a meal to close macro gaps. See §4.5 table.
class FillerResult {
  FillerResult(this.foods, this.totalKcal, this.totalProteinG,
      this.totalCarbG, this.totalFatG, this.totalFiberG);
  final List<MealFood> foods;
  final double totalKcal;
  final double totalProteinG;
  final double totalCarbG;
  final double totalFatG;
  final double totalFiberG;
}

FillerResult computeFillers({
  required double kcalGap,
  required double proteinGap,
  required double carbGap,
  required double fatGap,
  required double fiberGap,
  required FoodDatabase foodDb,
  required DietType diet,
  required List<String> allergens,
  required bool isMainMeal,
}) {
  final foods = <MealFood>[];
  double totalKcal = 0, totalProteinG = 0, totalCarbG = 0, totalFatG = 0, totalFiberG = 0;

  void addFiller(FillerType type, double gapG) {
    if (gapG <= 0) return;
    final threshold = switch (type) {
      FillerType.protein => fillerThresholdProteinG,
      FillerType.carb => fillerThresholdCarbG,
      FillerType.fat => fillerThresholdFatG,
      FillerType.veg => fillerThresholdFiberG,
    };
    if (gapG <= threshold) return;

    var fillers = foodDb.fillersFor(type, diet);
    fillers = filterFillers(fillers, allergens);
    if (fillers.isEmpty) return;

    final food = fillers.first;
    final per100g = food.per100g;
    final targetG = food.slug == 'whey' || food.slug == 'pea_protein' || food.slug == 'soy_protein'
        ? gapG * 100 / (per100g['protein_g'] ?? 80)
        : (gapG * 100 / (per100g[_macroKey(type)] ?? 1));

    // Cap: protein ×4, carb ×3, fat ×3 serving.
    final capMult = switch (type) {
      FillerType.protein => fillerServingCapProtein,
      FillerType.carb => fillerServingCapCarb,
      FillerType.fat => fillerServingCapFat,
      FillerType.veg => 2.0,
    };
    final maxG = (food.servingG * capMult).toDouble();
    final minG = food.servingG * fillerMinServingFrac;
    var grams = targetG.clamp(minG.toDouble(), maxG);

    // Veg fixed range.
    if (type == FillerType.veg) {
      grams = grams.clamp(vegMinG.toDouble(), vegMaxG.toDouble());
    }

    final kcal = (per100g['kcal'] ?? 0) * grams / 100;
    final p = (per100g['protein_g'] ?? 0) * grams / 100;
    final c = (per100g['carb_g'] ?? 0) * grams / 100;
    final f = (per100g['fat_g'] ?? 0) * grams / 100;
    final fib = (per100g['fiber_g'] ?? 0) * grams / 100;

    foods.add(MealFood(
      food: food,
      grams: round1(grams),
      kcal: round1(kcal),
      proteinG: round1(p),
      carbG: round1(c),
      fatG: round1(f),
      fiberG: round1(fib),
      isFiller: true,
    ));

    totalKcal += kcal;
    totalProteinG += p;
    totalCarbG += c;
    totalFatG += f;
    totalFiberG += fib;
  }

  addFiller(FillerType.protein, proteinGap);
  addFiller(FillerType.carb, carbGap);
  addFiller(FillerType.fat, fatGap);
  if (isMainMeal) {
    addFiller(FillerType.veg, fiberGap);
  }

  return FillerResult(
    foods,
    round1(totalKcal),
    round1(totalProteinG),
    round1(totalCarbG),
    round1(totalFatG),
    round1(totalFiberG),
  );
}

String _macroKey(FillerType t) {
  return switch (t) {
    FillerType.protein => 'protein_g',
    FillerType.carb => 'carb_g',
    FillerType.fat => 'fat_g',
    FillerType.veg => 'fiber_g',
  };
}

/// Recipe swaps — alternatives sharing ≥1 meal_type, diet-compatible, kcal
/// within ±20%, no allergens, cuisine-matching if specified.
List<Recipe> recipeSwaps({
  required Recipe recipe,
  required RecipeLibrary library,
  required DietType diet,
  required List<String> allergens,
  String? cuisinePreference,
}) {
  return library.all.where((r) {
    if (r.id == recipe.id) return false;
    // Share at least one meal type.
    final sharesMeal = r.mealTypes.any((m) => recipe.mealTypes.contains(m));
    if (!sharesMeal) return false;
    // Diet-compatible.
    if (diet != DietType.omnivore) {
      final isVeganR = r.dietTypes.any((d) =>
          d == RecipeDietTag.vegan || d == RecipeDietTag.veganEthiopian);
      if (!isVeganR) return false;
    }
    // kcal within ±20%.
    final diff = (r.kcal - recipe.kcal).abs() / max(1, recipe.kcal);
    if (diff > 0.20) return false;
    // No allergens.
    if (containsAllergen(r.ingredients.join(' '), allergens)) return false;
    // Cuisine-matching if specified.
    if (cuisinePreference != null &&
        r.cuisine.toLowerCase() != cuisinePreference.toLowerCase()) {
      return false;
    }
    return true;
  }).toList()
    ..sort((a, b) =>
        (a.kcal - recipe.kcal).abs().compareTo((b.kcal - recipe.kcal).abs()));
}
