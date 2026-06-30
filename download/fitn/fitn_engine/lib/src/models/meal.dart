/// Meal plan output models. See spec §9.1 (output tree).
library;

import 'enums.dart';

/// A food item from `food_database.json` (used for fillers).
class FoodItem {
  FoodItem({
    required this.slug,
    required this.name,
    required this.category,
    required this.servingG,
    required this.per100g,
  });

  final String slug;
  final String name;
  final FoodCategory category;
  final int servingG;
  final Map<String, double> per100g; // kcal, protein_g, carb_g, fat_g, fiber_g

  factory FoodItem.fromJson(Map<String, dynamic> json) {
    return FoodItem(
      slug: json['slug'] as String,
      name: json['name'] as String,
      category: FoodCategoryJson.fromJson(json['category'] as String),
      servingG: (json['serving_g'] as num).toInt(),
      per100g: (json['per_100g'] as Map).map((k, v) =>
          MapEntry(k as String, (v as num).toDouble())),
    );
  }

  Map<String, dynamic> toJson() => {
        'slug': slug,
        'name': name,
        'category': category.toJson(),
        'serving_g': servingG,
        'per_100g': per100g,
      };
}

class Recipe {
  Recipe({
    required this.id,
    required this.name,
    required this.source,
    required this.cuisine,
    required this.mealTypes,
    required this.dietTypes,
    required this.servings,
    required this.prepTimeMin,
    required this.cookTimeMin,
    required this.ingredients,
    required this.instructions,
    required this.nutritionPerServing,
    required this.nutritionSource,
    required this.proteinDensity,
    required this.calorieDensity,
    required this.allergens,
    required this.goalFit,
    required this.fastingYetsom,
    required this.injeraAccompaniment,
    required this.imageUrl,
    required this.alternativeRecipeIds,
    required this.notes,
    this.selectionReason,
    this.isCurated = false,
    this.topAlternatives = const [],
  });

  final String id;
  final String name;
  final String source;
  final String cuisine;
  final List<MealType> mealTypes;
  final List<RecipeDietTag> dietTypes;
  final int servings;
  final int prepTimeMin;
  final int cookTimeMin;
  final List<String> ingredients;
  final List<String> instructions;
  final Map<String, double> nutritionPerServing; // kcal, protein_g, carb_g, fat_g, fiber_g, sugar_g
  final String nutritionSource; // "published" | "calculated"
  final String proteinDensity; // "low" | "medium" | "high"
  final String calorieDensity;
  final List<String> allergens;
  final List<String> goalFit;
  final bool fastingYetsom;
  final bool injeraAccompaniment;
  final String imageUrl;
  final List<String> alternativeRecipeIds;
  final String notes;
  final String? selectionReason;
  final bool isCurated;
  final List<Map<String, dynamic>> topAlternatives;

  double get kcal => nutritionPerServing['kcal'] ?? 0;
  double get proteinG => nutritionPerServing['protein_g'] ?? 0;
  double get carbG => nutritionPerServing['carb_g'] ?? 0;
  double get fatG => nutritionPerServing['fat_g'] ?? 0;
  double get fiberG => nutritionPerServing['fiber_g'] ?? 0;
  double get sugarG => nutritionPerServing['sugar_g'] ?? 0;

  factory Recipe.fromJson(Map<String, dynamic> json) {
    return Recipe(
      id: json['id'] as String,
      name: json['name'] as String,
      source: json['source'] as String? ?? '',
      cuisine: json['cuisine'] as String? ?? '',
      mealTypes: ((json['meal_types'] as List?) ?? const [])
          .map((e) => _mealTypeFromString(e as String))
          .toList(),
      dietTypes: ((json['diet_types'] as List?) ?? const [])
          .map((e) => RecipeDietTagJson.fromJsonScreaming(e as String))
          .toList(),
      servings: (json['servings'] as num? ?? 1).toInt(),
      prepTimeMin: (json['prep_time_min'] as num? ?? 0).toInt(),
      cookTimeMin: (json['cook_time_min'] as num? ?? 0).toInt(),
      ingredients: ((json['ingredients'] as List?) ?? const [])
          .map((e) => e as String)
          .toList(),
      instructions: ((json['instructions'] as List?) ?? const [])
          .map((e) => e as String)
          .toList(),
      nutritionPerServing:
          (json['nutrition_per_serving'] as Map).map((k, v) =>
              MapEntry(k as String, (v as num?)?.toDouble() ?? 0.0)),
      nutritionSource: json['nutrition_source'] as String? ?? 'published',
      proteinDensity: json['protein_density'] as String? ?? 'medium',
      calorieDensity: json['calorie_density'] as String? ?? 'medium',
      allergens: ((json['allergens'] as List?) ?? const [])
          .map((e) => e as String)
          .toList(),
      goalFit: ((json['goal_fit'] as List?) ?? const [])
          .map((e) => e as String)
          .toList(),
      fastingYetsom: (json['fasting_yetsom'] as bool? ?? false),
      injeraAccompaniment: (json['injera_accompaniment'] as bool? ?? false),
      imageUrl: json['image_url'] as String? ?? '',
      alternativeRecipeIds: ((json['alternative_recipe_ids'] as List?) ??
              const [])
          .map((e) => e as String)
          .toList(),
      notes: json['notes'] as String? ?? '',
      selectionReason: json['selection_reason'] as String?,
      isCurated: (json['is_curated'] as bool? ?? false) ||
          (json['notes'] as String? ?? '').contains('[curated]'),
      topAlternatives: ((json['top_alternatives'] as List?) ?? const [])
          .map((e) => e as Map<String, dynamic>)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'source': source,
        'cuisine': cuisine,
        'meal_types': mealTypes.map((e) => _mealTypeToString(e)).toList(),
        'diet_types':
            dietTypes.map((e) => e.toJsonScreaming()).toList(),
        'servings': servings,
        'prep_time_min': prepTimeMin,
        'cook_time_min': cookTimeMin,
        'ingredients': ingredients,
        'instructions': instructions,
        'nutrition_per_serving': nutritionPerServing,
        'nutrition_source': nutritionSource,
        'protein_density': proteinDensity,
        'calorie_density': calorieDensity,
        'allergens': allergens,
        'goal_fit': goalFit,
        'fasting_yetsom': fastingYetsom,
        'injera_accompaniment': injeraAccompaniment,
        'image_url': imageUrl,
        'alternative_recipe_ids': alternativeRecipeIds,
        'notes': notes,
        'selection_reason': selectionReason,
        'top_alternatives': topAlternatives,
      };
}

class MealFood {
  MealFood({
    required this.food,
    required this.grams,
    required this.kcal,
    required this.proteinG,
    required this.carbG,
    required this.fatG,
    required this.fiberG,
    required this.isFiller,
  });

  final FoodItem food;
  final double grams;
  final double kcal;
  final double proteinG;
  final double carbG;
  final double fatG;
  final double fiberG;
  final bool isFiller;

  Map<String, dynamic> toJson() => {
        'food': food.toJson(),
        'grams': grams,
        'kcal': kcal,
        'protein_g': proteinG,
        'carb_g': carbG,
        'fat_g': fatG,
        'fiber_g': fiberG,
        'is_filler': isFiller,
      };

  factory MealFood.fromJson(Map<String, dynamic> json) {
    return MealFood(
      food: FoodItem.fromJson(json['food'] as Map<String, dynamic>),
      grams: (json['grams'] as num).toDouble(),
      kcal: (json['kcal'] as num).toDouble(),
      proteinG: (json['protein_g'] as num).toDouble(),
      carbG: (json['carb_g'] as num).toDouble(),
      fatG: (json['fat_g'] as num).toDouble(),
      fiberG: (json['fiber_g'] as num).toDouble(),
      isFiller: (json['is_filler'] as bool? ?? false),
    );
  }
}

class Meal {
  Meal({
    required this.mealType,
    required this.name,
    required this.foods,
    this.recipe,
    required this.scaleFactor,
    required this.scaledNutrition,
    required this.targetKcal,
    required this.targetProteinG,
    required this.targetCarbG,
    required this.targetFatG,
    required this.actualKcal,
    required this.actualProteinG,
    required this.actualCarbG,
    required this.actualFatG,
    required this.selectionReason,
    required this.notes,
  });

  final MealType mealType;
  final String name;
  final List<MealFood> foods;
  final Recipe? recipe;
  final double scaleFactor;
  final Map<String, double> scaledNutrition;
  final double targetKcal;
  final double targetProteinG;
  final double targetCarbG;
  final double targetFatG;
  final double actualKcal;
  final double actualProteinG;
  final double actualCarbG;
  final double actualFatG;
  final String selectionReason;
  final List<String> notes;

  /// Computed: total fiber from scaled recipe + fillers.
  double get actualFiberG {
    final scaledFiber = scaledNutrition['fiber_g'] ?? 0;
    final fillersFiber = foods.fold(0.0, (s, f) => s + f.fiberG);
    return scaledFiber + fillersFiber;
  }

  Map<String, dynamic> toJson() => {
        'meal_type': mealType.toJson(),
        'name': name,
        'foods': foods.map((e) => e.toJson()).toList(),
        'recipe': recipe?.toJson(),
        'scale_factor': scaleFactor,
        'scaled_nutrition': scaledNutrition,
        'target_kcal': targetKcal,
        'target_protein_g': targetProteinG,
        'target_carb_g': targetCarbG,
        'target_fat_g': targetFatG,
        'actual_kcal': actualKcal,
        'actual_protein_g': actualProteinG,
        'actual_carb_g': actualCarbG,
        'actual_fat_g': actualFatG,
        'selection_reason': selectionReason,
        'notes': notes,
      };

  factory Meal.fromJson(Map<String, dynamic> json) {
    return Meal(
      mealType: MealTypeJson.fromJson(json['meal_type'] as String),
      name: json['name'] as String,
      foods: ((json['foods'] as List?) ?? const [])
          .map((e) => MealFood.fromJson(e as Map<String, dynamic>))
          .toList(),
      recipe: json['recipe'] != null
          ? Recipe.fromJson(json['recipe'] as Map<String, dynamic>)
          : null,
      scaleFactor: (json['scale_factor'] as num? ?? 1.0).toDouble(),
      scaledNutrition: (json['scaled_nutrition'] as Map? ?? {}).map(
          (k, v) => MapEntry(k as String, (v as num).toDouble())),
      targetKcal: (json['target_kcal'] as num? ?? 0).toDouble(),
      targetProteinG: (json['target_protein_g'] as num? ?? 0).toDouble(),
      targetCarbG: (json['target_carb_g'] as num? ?? 0).toDouble(),
      targetFatG: (json['target_fat_g'] as num? ?? 0).toDouble(),
      actualKcal: (json['actual_kcal'] as num? ?? 0).toDouble(),
      actualProteinG: (json['actual_protein_g'] as num? ?? 0).toDouble(),
      actualCarbG: (json['actual_carb_g'] as num? ?? 0).toDouble(),
      actualFatG: (json['actual_fat_g'] as num? ?? 0).toDouble(),
      selectionReason: json['selection_reason'] as String? ?? '',
      notes: (json['notes'] as List? ?? const []).cast<String>(),
    );
  }
}

class DayPlan {
  DayPlan({
    required this.dayNumber,
    required this.dayName,
    required this.meals,
    required this.isTrainingDay,
    required this.totalKcal,
    required this.totalProteinG,
    required this.totalCarbG,
    required this.totalFatG,
    required this.totalFiberG,
  });

  final int dayNumber;
  final String dayName;
  final List<Meal> meals;
  final bool isTrainingDay;
  final double totalKcal;
  final double totalProteinG;
  final double totalCarbG;
  final double totalFatG;
  final double totalFiberG;

  Map<String, dynamic> toJson() => {
        'day_number': dayNumber,
        'day_name': dayName,
        'meals': meals.map((e) => e.toJson()).toList(),
        'is_training_day': isTrainingDay,
        'total_kcal': totalKcal,
        'total_protein_g': totalProteinG,
        'total_carb_g': totalCarbG,
        'total_fat_g': totalFatG,
        'total_fiber_g': totalFiberG,
      };

  factory DayPlan.fromJson(Map<String, dynamic> json) {
    return DayPlan(
      dayNumber: (json['day_number'] as num).toInt(),
      dayName: json['day_name'] as String,
      meals: ((json['meals'] as List?) ?? const [])
          .map((e) => Meal.fromJson(e as Map<String, dynamic>))
          .toList(),
      isTrainingDay: (json['is_training_day'] as bool? ?? false),
      totalKcal: (json['total_kcal'] as num? ?? 0).toDouble(),
      totalProteinG: (json['total_protein_g'] as num? ?? 0).toDouble(),
      totalCarbG: (json['total_carb_g'] as num? ?? 0).toDouble(),
      totalFatG: (json['total_fat_g'] as num? ?? 0).toDouble(),
      totalFiberG: (json['total_fiber_g'] as num? ?? 0).toDouble(),
    );
  }
}

class RecipeSourceSummary {
  RecipeSourceSummary({
    required this.curatedUsed,
    required this.uncuratedUsed,
    required this.fallbackToRawFoods,
    required this.uniqueRecipesUsed,
    required this.databaseTotal,
    required this.databaseCurated,
    required this.databaseUncurated,
    this.weeklyAvgKcalMatchPct,
    this.weeklyAvgProteinMatchPct,
    required this.trainingDays,
    required this.includePrePostWorkout,
  });

  final int curatedUsed;
  final int uncuratedUsed;
  final int fallbackToRawFoods;
  final int uniqueRecipesUsed;
  final int databaseTotal;
  final int databaseCurated;
  final int databaseUncurated;
  final double? weeklyAvgKcalMatchPct;
  final double? weeklyAvgProteinMatchPct;
  final List<int> trainingDays;
  final bool includePrePostWorkout;

  Map<String, dynamic> toJson() => {
        'curated_used': curatedUsed,
        'uncurated_used': uncuratedUsed,
        'fallback_to_raw_foods': fallbackToRawFoods,
        'unique_recipes_used': uniqueRecipesUsed,
        'database_total': databaseTotal,
        'database_curated': databaseCurated,
        'database_uncurated': databaseUncurated,
        'weekly_avg_kcal_match_pct': weeklyAvgKcalMatchPct,
        'weekly_avg_protein_match_pct': weeklyAvgProteinMatchPct,
        'training_days': trainingDays,
        'include_pre_post_workout': includePrePostWorkout,
      };

  factory RecipeSourceSummary.fromJson(Map<String, dynamic> json) {
    return RecipeSourceSummary(
      curatedUsed: (json['curated_used'] as num? ?? 0).toInt(),
      uncuratedUsed: (json['uncurated_used'] as num? ?? 0).toInt(),
      fallbackToRawFoods:
          (json['fallback_to_raw_foods'] as num? ?? 0).toInt(),
      uniqueRecipesUsed:
          (json['unique_recipes_used'] as num? ?? 0).toInt(),
      databaseTotal: (json['database_total'] as num? ?? 0).toInt(),
      databaseCurated: (json['database_curated'] as num? ?? 0).toInt(),
      databaseUncurated:
          (json['database_uncurated'] as num? ?? 0).toInt(),
      weeklyAvgKcalMatchPct:
          (json['weekly_avg_kcal_match_pct'] as num?)?.toDouble(),
      weeklyAvgProteinMatchPct:
          (json['weekly_avg_protein_match_pct'] as num?)?.toDouble(),
      trainingDays: ((json['training_days'] as List?) ?? const [])
          .map((e) => (e as num).toInt())
          .toList(),
      includePrePostWorkout:
          (json['include_pre_post_workout'] as bool? ?? false),
    );
  }
}

class MealPlan {
  MealPlan({
    required this.days,
    required this.mealFrequency,
    required this.macroAllocation,
    required this.cuisineMix,
    required this.recipeSourceSummary,
    required this.notes,
  });

  final List<DayPlan> days; // exactly 7
  final int mealFrequency;
  final Map<String, double> macroAllocation;
  final Map<String, int> cuisineMix;
  final RecipeSourceSummary recipeSourceSummary;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'days': days.map((e) => e.toJson()).toList(),
        'meal_frequency': mealFrequency,
        'macro_allocation': macroAllocation,
        'cuisine_mix': cuisineMix,
        'recipe_source_summary': recipeSourceSummary.toJson(),
        'notes': notes,
      };

  factory MealPlan.fromJson(Map<String, dynamic> json) {
    return MealPlan(
      days: ((json['days'] as List?) ?? const [])
          .map((e) => DayPlan.fromJson(e as Map<String, dynamic>))
          .toList(),
      mealFrequency: (json['meal_frequency'] as num? ?? 3).toInt(),
      macroAllocation: (json['macro_allocation'] as Map? ?? {}).map(
          (k, v) => MapEntry(k as String, (v as num).toDouble())),
      cuisineMix: (json['cuisine_mix'] as Map? ?? {}).map(
          (k, v) => MapEntry(k as String, (v as num).toInt())),
      recipeSourceSummary: RecipeSourceSummary.fromJson(
          json['recipe_source_summary'] as Map<String, dynamic>? ?? {}),
      notes: (json['notes'] as List? ?? const []).cast<String>(),
    );
  }
}

// === String ↔ MealType helpers ===

MealType _mealTypeFromString(String s) {
  final lower = s.toLowerCase();
  return switch (lower) {
    'breakfast' => MealType.breakfast,
    'lunch' => MealType.lunch,
    'dinner' => MealType.dinner,
    'snack' => MealType.snack,
    'side' => MealType.side,
    'pre_workout' => MealType.preWorkout,
    'post_workout' => MealType.postWorkout,
    _ => MealType.snack,
  };
}

String _mealTypeToString(MealType t) {
  return switch (t) {
    MealType.breakfast => 'breakfast',
    MealType.lunch => 'lunch',
    MealType.dinner => 'dinner',
    MealType.snack => 'snack',
    MealType.side => 'side',
    MealType.preWorkout => 'pre_workout',
    MealType.postWorkout => 'post_workout',
  };
}
