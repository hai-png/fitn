/// Food database loader + filler options. See spec §4.5.
library;

import 'dart:convert';
import 'dart:io';

import '../models/meal.dart';
import '../models/enums.dart';

class FoodDatabase {
  FoodDatabase(this._foods)
      : _bySlug = {for (final f in _foods) f.slug: f};

  final List<FoodItem> _foods;
  final Map<String, FoodItem> _bySlug;

  List<FoodItem> get all => List.unmodifiable(_foods);
  FoodItem? bySlug(String slug) => _bySlug[slug];

  /// Filler options per category + diet type. See §4.5 table.
  ///
  /// For VEGAN prefix match — VEGAN_ETHIOPIAN resolves to VEGAN list.
  List<FoodItem> fillersFor(FillerType type, DietType diet) {
    final slugs = fillerSlugs(type, diet);
    return slugs.map((s) => _bySlug[s]).whereType<FoodItem>().toList();
  }
}

enum FillerType { protein, carb, fat, veg }

/// Static filler slug lists. See §4.5 table.
List<String> fillerSlugs(FillerType type, DietType diet) {
  // VEGAN prefix match — both vegan and vegan_ethiopian use vegan list.
  final isVegan = diet == DietType.vegan;

  switch (type) {
    case FillerType.protein:
      return isVegan
          ? const ['tofu', 'tempeh', 'pea_protein', 'soy_protein', 'lentils']
          : const [
              'whey', 'greek_yogurt', 'egg_white', 'cottage_cheese',
              'chicken_breast'
            ];
    case FillerType.carb:
      return const [
        'white_rice', 'brown_rice', 'oats', 'banana',
        'whole_wheat_bread', 'quinoa', 'sweet_potato'
      ];
    case FillerType.fat:
      return const [
        'olive_oil', 'almonds', 'peanut_butter', 'walnuts', 'avocado'
      ];
    case FillerType.veg:
      return const [
        'broccoli', 'spinach', 'mixed_greens', 'bell_pepper',
        'asparagus', 'green_beans', 'carrots'
      ];
  }
}

/// Allergen → filler exclusion map. See §4.5.
const Map<String, Set<String>> allergenFillerExclusion = {
  'dairy': {'whey', 'greek_yogurt', 'cottage_cheese', 'milk', 'cheddar'},
  'eggs': {'egg_white'},
  'gluten': {'whole_wheat_bread', 'oats'},
  'nuts': {'almonds', 'walnuts'},
  'peanuts': {'peanut_butter'},
  'soy': {'tofu', 'tempeh', 'soy_protein'},
};

/// Filter out fillers excluded by allergens.
List<FoodItem> filterFillers(
    List<FoodItem> fillers, List<String> allergens) {
  if (allergens.isEmpty) return fillers;
  final excluded = <String>{};
  for (final a in allergens) {
    final lower = a.toLowerCase();
    final set = allergenFillerExclusion[lower] ??
        allergenFillerExclusion[lower.replaceAll(' ', '_')] ??
        allergenFillerExclusion[lower.replaceAll('_', ' ')] ??
        const {};
    excluded.addAll(set);
  }
  return fillers.where((f) => !excluded.contains(f.slug)).toList();
}

/// Load food database from `food_database.json`.
FoodDatabase loadFoodDatabase(String jsonStr) {
  final decoded = jsonDecode(jsonStr) as Map<String, dynamic>;
  final foods = <FoodItem>[];
  for (final entry in decoded.entries) {
    final food = FoodItem.fromJson(entry.value as Map<String, dynamic>);
    foods.add(food);
  }
  return FoodDatabase(foods);
}

Future<FoodDatabase> loadFoodDatabaseFromFile(String path) async {
  final file = File(path);
  final contents = await file.readAsString();
  return loadFoodDatabase(contents);
}
