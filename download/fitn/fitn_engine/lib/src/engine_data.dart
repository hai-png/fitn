/// Engine data loader. Loads all JSON data files from `assets/`.
library;

import 'dart:convert';
import 'dart:io';

import '../fitn_engine.dart';
import '../src/training/exercise_library.dart';
import '../src/training/split_designs.dart';
import '../src/meal_plan/food_database.dart';
import '../src/meal_plan/recipe_loader.dart';

/// Load engine data from the assets directory.
///
/// Tries the following base paths in order:
/// 1. [basePath] if provided.
/// 2. `<cwd>/assets/`.
/// 3. `<cwd>/fitn_engine/assets/` (when run from project root).
/// 4. `<script dir>/assets/` (when run from tests).
Future<EngineData> loadEngineData({String? basePath}) async {
  final candidates = <String>[
    if (basePath != null) basePath,
    '${Directory.current.path}/assets',
    '${Directory.current.path}/fitn_engine/assets',
    '${Platform.script.resolve('assets').path}',
  ];

  String? assetDir;
  for (final c in candidates) {
    if (await Directory(c).exists()) {
      assetDir = c;
      break;
    }
  }
  if (assetDir == null) {
    throw FileSystemException(
        'Could not find engine assets directory. Tried: ${candidates.join(", ")}');
  }

  Future<String?> readIfExists(String name) async {
    final f = File('$assetDir/$name');
    if (await f.exists()) return await f.readAsString();
    return null;
  }

  // all_exercises.json (required).
  final exercisesJson = await readIfExists('all_exercises.json');
  if (exercisesJson == null) {
    throw FileSystemException(
        'Missing required file: all_exercises.json in $assetDir');
  }
  final exerciseLibrary = loadExerciseLibrary(exercisesJson);

  // split_designs.json (required).
  final splitsJson = await readIfExists('split_designs.json');
  if (splitsJson == null) {
    throw FileSystemException(
        'Missing required file: split_designs.json in $assetDir');
  }
  final splits = loadSplitDesigns(splitsJson);

  // movement_patterns.json (required).
  final patternsJson = await readIfExists('movement_patterns.json');
  if (patternsJson == null) {
    throw FileSystemException(
        'Missing required file: movement_patterns.json in $assetDir');
  }
  final patternsMap = jsonDecode(patternsJson) as Map<String, dynamic>;
  final patterns = patternsMap.map((k, v) => MapEntry(
      k, MovementPatternSpec.fromJson(k, v as Map<String, dynamic>)));

  // food_database.json (required).
  final foodsJson = await readIfExists('food_database.json');
  if (foodsJson == null) {
    throw FileSystemException(
        'Missing required file: food_database.json in $assetDir');
  }
  final foodDb = loadFoodDatabase(foodsJson);

  // Recipes — curated may be missing; uncurated + pre/post required.
  final curatedJson = await readIfExists('recipe_database.json');
  final uncuratedJson = await readIfExists('recipe_database_uncurated.json');
  final prePostJson = await readIfExists('pre_post_workout_recipes.json');
  final recipeLibrary = loadRecipeLibrary(
    curatedJson: curatedJson,
    uncuratedJson: uncuratedJson,
    prePostJson: prePostJson,
  );

  return EngineData(
    exercises: exerciseLibrary.all,
    splits: splits,
    movementPatterns: patterns,
    recipes: recipeLibrary.all,
    foodDatabase: {for (final f in foodDb.all) f.slug: f},
  );
}
