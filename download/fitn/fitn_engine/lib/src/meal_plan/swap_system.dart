import 'package:fitn_engine/src/meal_plan/allergen_constants.dart';
import 'package:fitn_engine/src/models/meal.dart';

/// Swap system. Spec §4.5.
///
/// Recipe swaps: alternatives sharing ≥1 meal_type, diet-compatible,
/// kcal within ±20%, no allergens, cuisine-matching if specified.
/// Sorted by kcal closeness, limited to 5.
///
/// Ingredient swaps: static substitution DB.

class RecipeSwap {
  final String id;
  final String name;
  final double kcal;
  final double proteinG;
  final String cuisine;
  final double similarity;

  const RecipeSwap({
    required this.id,
    required this.name,
    required this.kcal,
    required this.proteinG,
    required this.cuisine,
    required this.similarity,
  });
}

/// Find up to 5 alternative recipes for [source].
List<RecipeSwap> findRecipeSwaps({
  required Recipe source,
  required List<Recipe> allRecipes,
  required String dietTag,
  required List<String> allergensToAvoid,
  String? cuisinePreference,
}) {
  final isVeganUser = dietTag.toUpperCase() == 'VEGAN' ||
      dietTag.toUpperCase() == 'VEGETARIAN';
  final sourceKcal = source.nutritionPerServing.kcal;
  final sourceMealTypes = source.mealTypes.map((m) => m.name).toSet();

  final candidates = allRecipes.where((r) {
    if (r.id == source.id) return false;
    // Share ≥1 meal type.
    final rMeals = r.mealTypes.map((m) => m.name).toSet();
    if (rMeals.intersection(sourceMealTypes).isEmpty) return false;
    // Diet compatible.
    if (isVeganUser) {
      if (!r.dietTypes.any((d) =>
          d.name.toUpperCase() == 'VEGAN' ||
          d.name.toUpperCase() == 'VEGAN_ETHIOPIAN')) {
        return false;
      }
    }
    // Kcal ±20%.
    if (sourceKcal > 0) {
      final ratio = (r.nutritionPerServing.kcal - sourceKcal).abs() / sourceKcal;
      if (ratio > 0.20) return false;
    }
    // No allergens.
    if (containsAllergen(r.ingredients.join(' | '), allergensToAvoid)) return false;
    // Cuisine match if specified.
    if (cuisinePreference != null && r.cuisine != cuisinePreference) return false;
    return true;
  }).toList();

  // Sort by kcal closeness.
  candidates.sort((a, b) {
    final da = (a.nutritionPerServing.kcal - sourceKcal).abs();
    final db = (b.nutritionPerServing.kcal - sourceKcal).abs();
    return da.compareTo(db);
  });

  return candidates.take(5).map((r) {
    final da = (r.nutritionPerServing.kcal - sourceKcal).abs();
    final similarity = sourceKcal > 0 ? 1 - da / sourceKcal : 0.0;
    return RecipeSwap(
      id: r.id,
      name: r.name,
      kcal: r.nutritionPerServing.kcal,
      proteinG: r.nutritionPerServing.proteinG,
      cuisine: r.cuisine,
      similarity: similarity,
    );
  }).toList();
}

/// Static substitution database for ingredients.
/// Longest-key-first matching, plant-named-phrase protection.
const Map<String, String> INGREDIENT_SUBSTITUTIONS = {
  // Ethiopian ingredients.
  'niter kibbeh': 'vegan butter (or olive oil + spices)',
  'injera': 'gluten-free teff pancake (or rice wrap)',
  'berbere': 'blended chili + paprika + ginger + fenugreek',
  'mitmita': 'chili powder + cardamom + salt',
  'teff flour': 'sorghum flour (or rice flour)',
  // Proteins.
  'chicken breast': 'turkey breast (or seitan for vegan)',
  'beef': 'beyond beef (or lentils)',
  'pork': 'jackfruit (or mushrooms)',
  'fish': 'hearts of palm (or tofu)',
  'shrimp': 'king oyster mushroom',
  'eggs': 'flax egg (1 tbsp flax + 3 tbsp water)',
  'egg whites': 'aquafaba',
  'greek yogurt': 'coconut yogurt (or soy yogurt)',
  'whey protein': 'pea protein',
  'cottage cheese': 'tofu scramble',
  'milk': 'oat milk (or soy milk)',
  'butter': 'vegan butter (or coconut oil)',
  'cheddar': 'vegan cheddar (or nutritional yeast)',
  // Carbs.
  'white rice': 'cauliflower rice (or quinoa)',
  'brown rice': 'quinoa (or farro)',
  'pasta': 'zucchini noodles (or chickpea pasta)',
  'bread': 'gluten-free bread (or lettuce wrap)',
  'couscous': 'quinoa (or millet)',
  'oats': 'quinoa flakes (or buckwheat groats)',
  // Fats.
  'olive oil': 'avocado oil',
  'peanut butter': 'almond butter (or sunflower seed butter)',
  'almonds': 'sunflower seeds (or pumpkin seeds)',
  'walnuts': 'pecans (or sunflower seeds)',
  'avocado': 'hummus (or mashed edamame)',
  // Vegetables.
  'broccoli': 'cauliflower (or broccolini)',
  'spinach': 'kale (or chard)',
  'bell pepper': 'poblano (or celery)',
  'sweet potato': 'butternut squash (or pumpkin)',
};

/// Find the best substitution for an ingredient. Returns null if none.
String? substituteIngredient(String ingredient) {
  final lower = ingredient.toLowerCase();
  // Longest-key-first matching.
  final keys = INGREDIENT_SUBSTITUTIONS.keys.toList()
    ..sort((a, b) => b.length.compareTo(a.length));
  for (final key in keys) {
    if (lower.contains(key)) {
      // Plant-named-phrase protection.
      final sanitized = _sanitizePlantPhrases(lower);
      if (sanitized.contains(key)) {
        return INGREDIENT_SUBSTITUTIONS[key];
      }
    }
  }
  return null;
}

String _sanitizePlantPhrases(String text) {
  var sanitized = text;
  for (final phrase in PLANT_NAMED_PHRASES) {
    final p = phrase.toLowerCase();
    var idx = sanitized.indexOf(p);
    while (idx >= 0) {
      sanitized = sanitized.substring(0, idx) +
          ' ' * p.length +
          sanitized.substring(idx + p.length);
      idx = sanitized.indexOf(p, idx + p.length);
    }
  }
  return sanitized;
}
