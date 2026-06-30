/// Allergen constants + plant-qualifier suppression. See spec §9.2.
///
/// Best-in-class allergen scanning: `coconut milk` must NOT match the `dairy`
/// allergen. See §11.3.
library;

/// Plant qualifiers — substring match in 25-char context BEFORE allergen keyword.
const List<String> plantQualifiers = [
  'almond', 'soy', 'oat', 'rice', 'coconut', 'cashew', 'hemp', 'flax',
  'macadamia', 'pea', 'vegan', 'plant', 'dairy-free', 'dairy free',
  'non-dairy', 'nondairy', 'peanut', 'cocoa', 'shea', 'sunflower',
  'avocado', 'apple', 'agave', 'maple', 'date', 'molasses', 'vegenaise',
  'just egg', 'egg replacer', 'flax egg', 'chia egg', 'beyond',
  'impossible', 'gardein', 'tofu', 'tempeh', 'seitan', 'vegetable',
  'veggie', 'mushroom', 'no-chicken', 'no chicken', 'chicken-style',
  'chicken style', 'vegan beef', 'vegan chicken', 'vegan pork',
  'vegan fish',
];

/// Plant-named phrases — blank out with equal-length spaces BEFORE scanning.
const List<String> plantNamedPhrases = [
  'eggplant', 'eggsplant', 'butter lettuce', 'butterleaf',
  'buttercup squash', 'cocoa butter', 'shea butter', 'cream of tartar',
  'creamed corn', 'coconut cream', 'almond butter', 'peanut butter',
  'cashew butter', 'sunflower butter', 'apple butter', 'pumpkin butter',
  'milk thistle', 'milkweed', 'honeydew', 'honeycrisp', 'broth of',
  'just egg', 'just eggs', 'flax egg', 'flax eggs', 'chia egg',
  'chia eggs', 'egg replacer', 'egg substitute', 'vegan egg',
  'vegan eggs', 'almond milk', 'soy milk', 'oat milk', 'rice milk',
  'coconut milk', 'cashew milk', 'hemp milk', 'macadamia milk',
  'pea milk', 'nutmeg', 'coconut', 'hazelnut', 'peanut', 'brazil nut',
  'walnut', 'pecan', 'almond', 'cashew', 'pistachio', 'macadamia',
];

/// Allergen → keyword map. See §9.2.
const Map<String, List<String>> allergenKeywords = {
  'dairy': [
    'milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'lactose',
    'ghee', 'kibbeh', 'niter kibbeh',
  ],
  'gluten': [
    'wheat', 'flour', 'bread', 'pasta', 'couscous', 'barley', 'rye',
    'seitan', 'bulgur', 'farro', 'spelt', 'injera',
  ],
  'soy': ['soy', 'tofu', 'tempeh', 'edamame', 'tamari', 'soy sauce', 'miso'],
  'nuts': [
    'almond', 'almonds', 'cashew', 'cashews', 'walnut', 'walnuts',
    'pecan', 'pecans', 'hazelnut', 'hazelnuts', 'pistachio', 'pistachios',
    'brazil nut', 'brazil nuts', 'macadamia', 'macadamias', 'pine nut',
    'pine nuts',
  ],
  'peanuts': ['peanut', 'groundnut'],
  'eggs': ['egg', 'eggs', 'mayonnaise', 'meringue'],
  'shellfish': [
    'shrimp', 'prawn', 'crab', 'lobster', 'crawfish', 'langoustine',
  ],
  'fish': [
    'salmon', 'tuna', 'cod', 'tilapia', 'sardine', 'anchovy', 'mackerel',
    'trout', 'halibut', 'fish',
  ],
  'sesame': ['sesame', 'tahini', 'sesame oil'],
  'corn': ['corn', 'cornstarch', 'corn syrup', 'cornmeal'],
};

/// Alias normalization. See §9.2.
String normalizeAllergen(String a) {
  final lower = a.toLowerCase();
  if (lower == 'tree_nuts' || lower == 'tree nuts' || lower == 'nuts') {
    return 'nuts';
  }
  if (lower == 'crustacean' || lower == 'crustaceans') {
    return 'shellfish';
  }
  return lower;
}

/// Sanitize an ingredient string by blanking out plant-named phrases.
String _sanitize(String text) {
  var result = text;
  for (final phrase in plantNamedPhrases) {
    final lower = result.toLowerCase();
    final idx = lower.indexOf(phrase);
    while (idx >= 0) {
      // Replace with equal-length spaces.
      final replacement = ' ' * phrase.length;
      result = result.substring(0, idx) +
          replacement +
          result.substring(idx + phrase.length);
      final newLower = result.toLowerCase();
      final nextIdx = newLower.indexOf(phrase, idx + phrase.length);
      if (nextIdx < 0) break;
      break; // Simple — handle one occurrence per phrase.
    }
  }
  return result;
}

/// Check if [ingredientsText] contains any of [allergens].
///
/// Plant-qualifier suppression: for `dairy` and `eggs`, check the 25-char
/// context before each match for a plant qualifier; if found, skip the match.
bool containsAllergen(String ingredientsText, List<String> allergens) {
  if (allergens.isEmpty) return false;
  final normalized = allergens.map(normalizeAllergen).toSet();

  // For dairy/eggs, sanitize first.
  final needsSanitization =
      normalized.contains('dairy') || normalized.contains('eggs');
  final sanitizedText =
      needsSanitization ? _sanitize(ingredientsText) : ingredientsText;

  for (final a in normalized) {
    final keywords = allergenKeywords[a];
    if (keywords == null) continue;
    final haystack = (a == 'dairy' || a == 'eggs')
        ? sanitizedText
        : ingredientsText;
    final haystackLower = haystack.toLowerCase();

    for (final kw in keywords) {
      final kwLower = kw.toLowerCase();
      var idx = haystackLower.indexOf(kwLower);
      while (idx >= 0) {
        if (a == 'dairy' || a == 'eggs') {
          // Check 25-char context before for plant qualifier.
          final start = (idx - 25).clamp(0, haystackLower.length);
          final context = haystackLower.substring(start, idx);
          bool hasQualifier = false;
          for (final q in plantQualifiers) {
            if (context.contains(q)) {
              hasQualifier = true;
              break;
            }
          }
          if (!hasQualifier) return true;
        } else {
          return true;
        }
        idx = haystackLower.indexOf(kwLower, idx + kwLower.length);
      }
    }
  }
  return false;
}
