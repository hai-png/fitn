import 'package:fitn_engine/src/meal_plan/allergen_constants.dart';
import 'package:fitn_engine/src/meal_plan/food_database.dart';
import 'package:fitn_engine/src/meal_plan/recipe_scorer.dart';
import 'package:fitn_engine/src/models/meal.dart';
import 'package:fitn_engine/src/utils/round.dart';

/// Recipe scaling + filler system. Spec §4.5.
///
/// scaleFactor = clamp(targetKcal / recipeKcal, 0.7, 1.5); 1.0 within ±10%.
/// Scaled nutrition = per-serving × scaleFactor.
///
/// Filler system: closes the macro gap after scaling.

/// Result of scaling a recipe.
class ScaledRecipe {
  final Recipe recipe;
  final double scaleFactor;
  final NutritionPerServing scaledNutrition;
  final List<MealFood> fillers;
  final NutritionPerServing totalNutrition;

  const ScaledRecipe({
    required this.recipe,
    required this.scaleFactor,
    required this.scaledNutrition,
    required this.fillers,
    required this.totalNutrition,
  });
}

/// Scale a recipe to the target kcal, then close the macro gap with fillers.
ScaledRecipe scaleRecipe({
  required Recipe recipe,
  required SlotTarget target,
  required String dietTag,
  required List<String> allergensToAvoid,
  required FoodDatabase foodDatabase,
  required bool isMainMeal,
}) {
  final recipeKcal = recipe.nutritionPerServing.kcal;
  double scale;
  if (recipeKcal <= 0) {
    scale = 1.0;
  } else {
    final ratio = target.kcal / recipeKcal;
    if ((ratio - 1.0).abs() <= 0.10) {
      scale = 1.0;
    } else {
      scale = ratio.clamp(0.7, 1.5).toDouble();
    }
  }

  final scaledKcal = recipe.nutritionPerServing.kcal * scale;
  final scaledProtein = recipe.nutritionPerServing.proteinG * scale;
  final scaledCarb = recipe.nutritionPerServing.carbG * scale;
  final scaledFat = recipe.nutritionPerServing.fatG * scale;
  final scaledFiber = recipe.nutritionPerServing.fiberG * scale;

  // Fillers — close the gap.
  final fillers = <MealFood>[];
  var totalKcal = scaledKcal;
  var totalProtein = scaledProtein;
  var totalCarb = scaledCarb;
  var totalFat = scaledFat;
  var totalFiber = scaledFiber;

  final system = FillerSystem.defaultFillers();

  // Protein gap.
  final proteinGap = target.proteinG - totalProtein;
  if (proteinGap > 5) {
    final filler = _pickFiller(
      category: dietTag.toUpperCase().startsWith('VEGAN')
          ? FoodCategory.proteinPlant
          : FoodCategory.proteinAnimal,
      dietTag: dietTag,
      allergens: allergensToAvoid,
      foodDatabase: foodDatabase,
      system: system,
      targetG: proteinGap,
      servingCapMult: 4,
    );
    if (filler != null) {
      fillers.add(filler);
      totalKcal += filler.kcal;
      totalProtein += filler.proteinG;
      totalCarb += filler.carbG;
      totalFat += filler.fatG;
      totalFiber += filler.fiberG;
    }
  }
  // Carb gap.
  final carbGap = target.carbG - totalCarb;
  if (carbGap > 5) {
    final filler = _pickFiller(
      category: FoodCategory.carbGrain,
      dietTag: dietTag,
      allergens: allergensToAvoid,
      foodDatabase: foodDatabase,
      system: system,
      targetG: carbGap,
      servingCapMult: 3,
    );
    if (filler != null) {
      fillers.add(filler);
      totalKcal += filler.kcal;
      totalProtein += filler.proteinG;
      totalCarb += filler.carbG;
      totalFat += filler.fatG;
      totalFiber += filler.fiberG;
    }
  }
  // Fat gap.
  final fatGap = target.fatG - totalFat;
  if (fatGap > 3) {
    final filler = _pickFiller(
      category: FoodCategory.fatOil,
      dietTag: dietTag,
      allergens: allergensToAvoid,
      foodDatabase: foodDatabase,
      system: system,
      targetG: fatGap,
      servingCapMult: 3,
    );
    if (filler != null) {
      fillers.add(filler);
      totalKcal += filler.kcal;
      totalProtein += filler.proteinG;
      totalCarb += filler.carbG;
      totalFat += filler.fatG;
      totalFiber += filler.fiberG;
    }
  }
  // Veg filler — main meals only, gap on fiber.
  if (isMainMeal) {
    final vegGap = target.fiberG - totalFiber;
    if (vegGap > 3) {
      final filler = _pickVegFiller(
        allergens: allergensToAvoid,
        foodDatabase: foodDatabase,
        system: system,
      );
      if (filler != null) {
        fillers.add(filler);
        totalKcal += filler.kcal;
        totalProtein += filler.proteinG;
        totalCarb += filler.carbG;
        totalFat += filler.fatG;
        totalFiber += filler.fiberG;
      }
    }
  }

  return ScaledRecipe(
    recipe: recipe,
    scaleFactor: roundBankers(scale, 4),
    scaledNutrition: NutritionPerServing(
      kcal: roundBankers(scaledKcal, 1),
      proteinG: roundBankers(scaledProtein, 1),
      carbG: roundBankers(scaledCarb, 1),
      fatG: roundBankers(scaledFat, 1),
      fiberG: roundBankers(scaledFiber, 1),
    ),
    fillers: fillers,
    totalNutrition: NutritionPerServing(
      kcal: roundBankers(totalKcal, 1),
      proteinG: roundBankers(totalProtein, 1),
      carbG: roundBankers(totalCarb, 1),
      fatG: roundBankers(totalFat, 1),
      fiberG: roundBankers(totalFiber, 1),
    ),
  );
}

MealFood? _pickFiller({
  required FoodCategory category,
  required String dietTag,
  required List<String> allergens,
  required FoodDatabase foodDatabase,
  required FillerSystem system,
  required double targetG,
  required int servingCapMult,
}) {
  final options = system.optionsFor(category, dietTag);
  for (final name in options) {
    // Allergen exclusion check.
    if (_isExcludedFiller(name, allergens)) continue;
    final food = foodDatabase.lookup(name);
    if (food == null) continue;
    final per100gProtein = food.per100gProteinG;
    if (per100gProtein <= 0 && category == FoodCategory.proteinAnimal) continue;
    if (food.per100gCarbG <= 0 && category == FoodCategory.carbGrain) continue;
    if (food.per100gFatG <= 0 && category == FoodCategory.fatOil) continue;
    // Compute grams needed.
    final per100g = switch (category) {
      FoodCategory.proteinAnimal || FoodCategory.proteinPlant => food.per100gProteinG,
      FoodCategory.carbGrain => food.per100gCarbG,
      FoodCategory.fatOil => food.per100gFatG,
      _ => 0.0,
    };
    if (per100g <= 0) continue;
    var grams = (targetG / per100g) * 100;
    final cap = food.servingG * servingCapMult;
    final minServing = food.servingG * 0.5;
    if (grams > cap) grams = cap;
    if (grams < minServing) grams = minServing;
    final kcal = (grams / 100) * food.per100gKcal;
    final protein = (grams / 100) * food.per100gProteinG;
    final carb = (grams / 100) * food.per100gCarbG;
    final fat = (grams / 100) * food.per100gFatG;
    final fiber = (grams / 100) * food.per100gFiberG;
    return MealFood(
      name: name,
      grams: roundBankers(grams, 1),
      kcal: roundBankers(kcal, 1),
      proteinG: roundBankers(protein, 1),
      carbG: roundBankers(carb, 1),
      fatG: roundBankers(fat, 1),
      fiberG: roundBankers(fiber, 1),
      category: category.name,
    );
  }
  return null;
}

MealFood? _pickVegFiller({
  required List<String> allergens,
  required FoodDatabase foodDatabase,
  required FillerSystem system,
}) {
  final options = system.optionsFor(FoodCategory.vegetable, 'OMNI');
  for (final name in options) {
    if (_isExcludedFiller(name, allergens)) continue;
    final food = foodDatabase.lookup(name);
    if (food == null) continue;
    // Veg: fixed [80g, 200g].
    final grams = 120.0;
    final kcal = (grams / 100) * food.per100gKcal;
    return MealFood(
      name: name,
      grams: roundBankers(grams, 1),
      kcal: roundBankers(kcal, 1),
      proteinG: roundBankers((grams / 100) * food.per100gProteinG, 1),
      carbG: roundBankers((grams / 100) * food.per100gCarbG, 1),
      fatG: roundBankers((grams / 100) * food.per100gFatG, 1),
      fiberG: roundBankers((grams / 100) * food.per100gFiberG, 1),
      category: FoodCategory.vegetable.name,
    );
  }
  return null;
}

bool _isExcludedFiller(String fillerName, List<String> allergens) {
  final nameLower = fillerName.toLowerCase();
  for (final a in allergens) {
    final normalized = normalizeAllergen(a);
    final excluded = ALLERGEN_FILLER_EXCLUSION[normalized];
    if (excluded == null) continue;
    for (final ex in excluded) {
      if (nameLower.contains(ex.toLowerCase())) return true;
    }
  }
  return false;
}
