/// Engine provider + plan generation wrapper + exercise/recipe data providers.
/// See spec §6.4.
library;

import 'dart:isolate';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';

import '../data/domain_types.dart';

/// Loads the engine once at app startup.
final engineProvider = FutureProvider<FitnEngine>((ref) async {
  final data = await loadEngineData();
  return FitnEngine(data: data);
});

/// The singleton engine data (kept loaded for passing to isolates).
EngineData? _engineDataSingleton;

Future<EngineData> getEngineData() async {
  _engineDataSingleton ??= await loadEngineData();
  return _engineDataSingleton!;
}

/// Generate a plan in an isolate (off the UI thread). See §6.4.
///
/// The engine is 200-500ms on a mid-range phone; isolating keeps the UI smooth.
Future<FitnessPlan> generatePlanInIsolate({
  required UserProfile profile,
  required PlanPreferences prefs,
  required EngineData engineData,
}) async {
  return Isolate.run(() {
    final engine = FitnEngine(data: engineData);
    final assessment = engine.assessProfile(profile);
    if (assessment.isPartial) {
      throw PartialAssessmentError(assessment.errors);
    }
    return engine.proposePlan(profile, assessment, prefs);
  });
}

/// Convenience: generate plan + assessment in one call (isolated).
Future<GeneratePlanResponse> generatePlanResponseInIsolate({
  required UserProfile profile,
  required PlanPreferences prefs,
  required EngineData engineData,
}) async {
  return Isolate.run(() {
    final engine = FitnEngine(data: engineData);
    return engine.generatePlan(profile, prefs);
  });
}

// =============================================================================
// EXERCISE DATABASE PROVIDERS
// =============================================================================

/// All 1,217 exercises from the engine, loaded once and cached.
final engineExercisesProvider =
    FutureProvider<List<Exercise>>((ref) async {
  final data = await getEngineData();
  return data.exercises;
});

/// Muscle categories derived from the exercise database (dynamic, not hardcoded).
final engineMuscleCategoriesProvider =
    FutureProvider<List<String>>((ref) async {
  final exercises = await ref.watch(engineExercisesProvider.future);
  final muscles = <String>{};
  for (final e in exercises) {
    for (final m in e.muscleGroups) {
      muscles.add(_normalizeMuscleCategory(m));
    }
  }
  // Sort by canonical order.
  final canonical = [
    'Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core', 'Cardio',
  ];
  final sorted = <String>[];
  for (final c in canonical) {
    if (muscles.contains(c)) sorted.add(c);
  }
  // Add any remaining muscles not in canonical list.
  for (final m in muscles) {
    if (!sorted.contains(m)) sorted.add(m);
  }
  return sorted;
});

/// Exercises filtered by muscle category.
final exercisesByMuscleProvider =
    FutureProvider.family<List<Exercise>, String>((ref, category) async {
  final exercises = await ref.watch(engineExercisesProvider.future);
  return exercises.where((e) {
    return e.muscleGroups.any((m) => _normalizeMuscleCategory(m) == category);
  }).toList();
});

/// Search exercises by name/slug/muscle.
final exerciseSearchProvider =
    FutureProvider.family<List<Exercise>, String>((ref, query) async {
  final exercises = await ref.watch(engineExercisesProvider.future);
  if (query.isEmpty) return exercises;
  final q = query.toLowerCase();
  return exercises.where((e) {
    return e.name.toLowerCase().contains(q) ||
        e.slug.toLowerCase().contains(q) ||
        e.muscleGroups.any((m) => m.toLowerCase().contains(q));
  }).toList();
});

/// Normalize a muscle name to a category.
/// e.g. "quads" → "Legs", "lats" → "Back", "side_delts" → "Shoulders".
String _normalizeMuscleCategory(String muscle) {
  final lower = muscle.toLowerCase();
  // Chest.
  if (['chest', 'upper chest', 'lower chest', 'pectorals'].contains(lower)) {
    return 'Chest';
  }
  // Back.
  if (['back', 'lats', 'mid back', 'middle_back', 'upper back', 'upper_back',
       'lower back', 'lower_back', 'traps', 'rear_delts', 'rear delts'].contains(lower)) {
    return 'Back';
  }
  // Legs.
  if (['quads', 'hamstrings', 'glutes', 'calves', 'adductors', 'abductors',
       'hip_flexors', 'legs'].contains(lower)) {
    return 'Legs';
  }
  // Shoulders.
  if (['shoulders', 'side_delts', 'side delts', 'front_delts', 'front delts',
       'deltoids'].contains(lower)) {
    return 'Shoulders';
  }
  // Arms.
  if (['biceps', 'triceps', 'forearms', 'arms', 'brachialis'].contains(lower)) {
    return 'Arms';
  }
  // Core.
  if (['abs', 'obliques', 'core', 'lower abs'].contains(lower)) {
    return 'Core';
  }
  // Cardio.
  if (['cardio'].contains(lower)) {
    return 'Cardio';
  }
  return 'Other';
}

// =============================================================================
// RECIPE DATABASE PROVIDERS (for meal ordering system)
// =============================================================================

/// All recipes from the engine (~225), converted to MealProduct format for the
/// meal ordering UI.
final engineMealRecipesProvider =
    FutureProvider<List<MealProduct>>((ref) async {
  final data = await getEngineData();
  return data.recipes.map(_recipeToMealProduct).toList();
});

/// Recipes filtered by meal type (breakfast/lunch/dinner/snack).
final recipesByMealTypeProvider =
    FutureProvider.family<List<MealProduct>, String>((ref, mealType) async {
  final all = await ref.watch(engineMealRecipesProvider.future);
  final mtLower = mealType.toLowerCase();
  return all.where((m) {
    // The MealProduct.category field stores the recipe's primary meal type.
    return m.category.toLowerCase() == mtLower;
  }).toList();
});

/// Convert an engine [Recipe] to a [MealProduct] for the ordering UI.
///
/// Generates a price based on calories (higher-calorie meals cost more,
/// reflecting ingredient quantity). Maps diet types to categories.
MealProduct _recipeToMealProduct(Recipe r) {
  // Generate price: $8-18 based on calorie density.
  final kcal = r.kcal;
  double price;
  if (kcal < 300) {
    price = 8.99;
  } else if (kcal < 450) {
    price = 11.99;
  } else if (kcal < 600) {
    price = 13.49;
  } else if (kcal < 750) {
    price = 14.99;
  } else {
    price = 16.99;
  }

  // Determine category from diet types.
  String category;
  if (r.dietTypes.any((d) =>
      d == RecipeDietTag.vegan || d == RecipeDietTag.veganEthiopian)) {
    category = 'vegan';
  } else if (r.dietTypes.any((d) => d == RecipeDietTag.vegetarian)) {
    category = 'vegetarian';
  } else {
    // Classify by macro profile.
    if (r.proteinG >= 30) {
      category = 'high-protein';
    } else if (r.carbG < 15) {
      category = 'low-carb';
    } else if (r.fatG >= 20 && r.carbG < 20) {
      category = 'keto';
    } else {
      category = 'balanced';
    }
  }

  // Build description from first 3 ingredients.
  final descIngredients = r.ingredients.take(3).join(', ');
  final description = descIngredients.isEmpty
      ? r.cuisine.isNotEmpty
          ? '${r.cuisine} cuisine • ${r.servings} servings'
          : '${r.servings} servings'
      : '$descIngredients${r.ingredients.length > 3 ? '...' : ''}';

  return MealProduct(
    id: r.id,
    name: r.name,
    description: description,
    price: price,
    calories: r.kcal.round(),
    protein: r.proteinG.round(),
    carbs: r.carbG.round(),
    fat: r.fatG.round(),
    image: r.imageUrl.isNotEmpty
        ? r.imageUrl
        : 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=80',
    category: category,
  );
}
