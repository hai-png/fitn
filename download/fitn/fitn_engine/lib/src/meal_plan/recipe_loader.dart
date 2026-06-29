/// Recipe loader. See spec §4.5 + §9.4.
///
/// Loads `recipe_database.json` + `recipe_database_uncurated.json` +
/// `pre_post_workout_recipes.json`. Apply sanitization:
/// - Rename uncurated ID collisions to `U<id>`.
/// - Append `[curated]` tag to curated recipes.
/// - VEGAN diet-warning (tagged VEGAN but ingredients contain meat/dairy/egg).
/// - kcal-warning (stated kcal vs macro-derived > 10% off).
library;

import 'dart:convert';
import 'dart:io';

import '../models/meal.dart';
import '../models/enums.dart';
import '../utils/units.dart';
import 'allergen_constants.dart';

class RecipeLibrary {
  RecipeLibrary(this._recipes)
      : _byId = {for (final r in _recipes) r.id: r},
        _byMealType = _indexByMealType(_recipes),
        _byDiet = _indexByDiet(_recipes);

  final List<Recipe> _recipes;
  final Map<String, Recipe> _byId;
  final Map<MealType, List<Recipe>> _byMealType;
  final Map<RecipeDietTag, List<Recipe>> _byDiet;

  List<Recipe> get all => List.unmodifiable(_recipes);
  int get count => _recipes.length;
  int get curatedCount => _recipes.where((r) => r.isCurated).length;
  int get uncuratedCount => _recipes.where((r) => !r.isCurated).length;

  Recipe? byId(String id) => _byId[id];

  List<Recipe> byMealType(MealType t) =>
      _byMealType[t] ?? const [];

  List<Recipe> byDiet(RecipeDietTag d) => _byDiet[d] ?? const [];

  /// Filter by diet compatibility (OMNI accepts all; VEGAN accepts VEGAN* only;
  /// VEGETARIAN accepts VEGAN* only — recipe DB has no vegetarian tag).
  List<Recipe> compatibleWith(DietType diet) {
    if (diet == DietType.omnivore) return all;
    // Vegetarian and vegan both fall to vegan recipes.
    return _recipes.where((r) {
      return r.dietTypes.any((d) {
        return d == RecipeDietTag.vegan ||
            d == RecipeDietTag.veganEthiopian;
      });
    }).toList();
  }

  static Map<MealType, List<Recipe>> _indexByMealType(List<Recipe> all) {
    final idx = <MealType, List<Recipe>>{};
    for (final r in all) {
      for (final mt in r.mealTypes) {
        idx.putIfAbsent(mt, () => []).add(r);
      }
    }
    return idx;
  }

  static Map<RecipeDietTag, List<Recipe>> _indexByDiet(List<Recipe> all) {
    final idx = <RecipeDietTag, List<Recipe>>{};
    for (final r in all) {
      for (final d in r.dietTypes) {
        idx.putIfAbsent(d, () => []).add(r);
      }
    }
    return idx;
  }
}

/// Load + sanitize the recipe library from multiple JSON files.
///
/// [curatedJson] may be null/empty if `recipe_database.json` is missing —
/// the engine tolerates this.
RecipeLibrary loadRecipeLibrary({
  String? curatedJson,
  String? uncuratedJson,
  String? prePostJson,
}) {
  final recipes = <Recipe>[];
  final seenIds = <String>{};

  // 1. Curated recipes.
  if (curatedJson != null && curatedJson.isNotEmpty) {
    final decoded = jsonDecode(curatedJson) as Map<String, dynamic>;
    final list = decoded['recipes'] as List? ?? const [];
    for (final r in list) {
      final recipe = _sanitizeRecipe(
          Recipe.fromJson(r as Map<String, dynamic>), isCurated: true);
      if (seenIds.add(recipe.id)) recipes.add(recipe);
    }
  }

  // 2. Uncurated recipes — rename ID collisions to U<id>.
  if (uncuratedJson != null && uncuratedJson.isNotEmpty) {
    final decoded = jsonDecode(uncuratedJson) as Map<String, dynamic>;
    final list = decoded['recipes'] as List? ?? const [];
    for (final r in list) {
      var recipe = Recipe.fromJson(r as Map<String, dynamic>);
      if (seenIds.contains(recipe.id)) {
        recipe = _withId(recipe, 'U${recipe.id}');
      }
      recipe = _sanitizeRecipe(recipe, isCurated: false);
      if (seenIds.add(recipe.id)) recipes.add(recipe);
    }
  }

  // 3. Pre/post workout recipes.
  if (prePostJson != null && prePostJson.isNotEmpty) {
    final decoded = jsonDecode(prePostJson) as Map<String, dynamic>;
    final list = decoded['recipes'] as List? ?? const [];
    for (final r in list) {
      var recipe = Recipe.fromJson(r as Map<String, dynamic>);
      if (seenIds.contains(recipe.id)) {
        recipe = _withId(recipe, 'PW-${recipe.id}');
      }
      recipe = _sanitizeRecipe(recipe, isCurated: false);
      if (seenIds.add(recipe.id)) recipes.add(recipe);
    }
  }

  return RecipeLibrary(recipes);
}

/// Apply sanitization: append [curated] tag, diet-warning, kcal-warning.
Recipe _sanitizeRecipe(Recipe r, {required bool isCurated}) {
  var notes = r.notes;
  if (isCurated && !notes.contains('[curated]')) {
    notes = '$notes [curated]';
  }

  // Diet warning: VEGAN-tagged recipe with meat/dairy/egg ingredients.
  final isVeganTagged = r.dietTypes.any((d) =>
      d == RecipeDietTag.vegan || d == RecipeDietTag.veganEthiopian);
  if (isVeganTagged) {
    final ingredientsText = r.ingredients.join(' ').toLowerCase();
    final hasMeat = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'lamb']
        .any((k) => ingredientsText.contains(k));
    final hasDairyOrEgg =
        containsAllergen(r.ingredients.join(' '), ['dairy', 'eggs']);
    if (hasMeat || hasDairyOrEgg) {
      notes =
          '$notes [diet-warning: tagged VEGAN but ingredients contain meat/dairy/egg — likely a curation error]';
    }
  }

  // kcal warning: stated vs macro-derived > 10% off.
  final p = r.proteinG * kcalPerGramProtein;
  final c = r.carbG * kcalPerGramCarb;
  final f = r.fatG * kcalPerGramFat;
  final derived = p + c + f;
  if (derived > 0) {
    final diff = (r.kcal - derived).abs() / derived;
    if (diff > 0.10) {
      notes =
          '$notes [kcal-warning: stated ${r.kcal.toStringAsFixed(0)} vs derived ${derived.toStringAsFixed(0)} — ${(diff * 100).toStringAsFixed(0)}% off]';
    }
  }

  if (notes == r.notes) return r;
  return _withNotes(r, notes);
}

Recipe _withId(Recipe r, String newId) {
  return Recipe(
    id: newId,
    name: r.name,
    source: r.source,
    cuisine: r.cuisine,
    mealTypes: r.mealTypes,
    dietTypes: r.dietTypes,
    servings: r.servings,
    prepTimeMin: r.prepTimeMin,
    cookTimeMin: r.cookTimeMin,
    ingredients: r.ingredients,
    instructions: r.instructions,
    nutritionPerServing: r.nutritionPerServing,
    nutritionSource: r.nutritionSource,
    proteinDensity: r.proteinDensity,
    calorieDensity: r.calorieDensity,
    allergens: r.allergens,
    goalFit: r.goalFit,
    fastingYetsom: r.fastingYetsom,
    injeraAccompaniment: r.injeraAccompaniment,
    imageUrl: r.imageUrl,
    alternativeRecipeIds: r.alternativeRecipeIds,
    notes: r.notes,
    selectionReason: r.selectionReason,
    isCurated: r.isCurated,
    topAlternatives: r.topAlternatives,
  );
}

Recipe _withNotes(Recipe r, String notes) {
  return Recipe(
    id: r.id,
    name: r.name,
    source: r.source,
    cuisine: r.cuisine,
    mealTypes: r.mealTypes,
    dietTypes: r.dietTypes,
    servings: r.servings,
    prepTimeMin: r.prepTimeMin,
    cookTimeMin: r.cookTimeMin,
    ingredients: r.ingredients,
    instructions: r.instructions,
    nutritionPerServing: r.nutritionPerServing,
    nutritionSource: r.nutritionSource,
    proteinDensity: r.proteinDensity,
    calorieDensity: r.calorieDensity,
    allergens: r.allergens,
    goalFit: r.goalFit,
    fastingYetsom: r.fastingYetsom,
    injeraAccompaniment: r.injeraAccompaniment,
    imageUrl: r.imageUrl,
    alternativeRecipeIds: r.alternativeRecipeIds,
    notes: notes,
    selectionReason: r.selectionReason,
    isCurated: r.isCurated,
    topAlternatives: r.topAlternatives,
  );
}

Future<RecipeLibrary> loadRecipeLibraryFromFiles({
  String? curatedPath,
  String? uncuratedPath,
  String? prePostPath,
}) async {
  String? read(String? path) =>
      path == null ? null : (await File(path).readAsString());
  return loadRecipeLibrary(
    curatedJson: await read(curatedPath),
    uncuratedJson: await read(uncuratedPath),
    prePostJson: await read(prePostPath),
  );
}
