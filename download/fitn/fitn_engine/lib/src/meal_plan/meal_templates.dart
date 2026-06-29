/// Meal templates: name cycling per day + meal-type allocation. See §4.5.
library;

import '../models/enums.dart';

/// Meal-type allocation by frequency. See §4.5 step 1.
///
/// 2 meals → LUNCH 0.50, DINNER 0.50 (no breakfast — intentional).
/// 3 meals → BREAKFAST 0.30, LUNCH 0.35, DINNER 0.35.
/// 4 meals → BREAKFAST 0.25, LUNCH 0.30, DINNER 0.30, SNACK 0.15.
/// 5 meals → BREAKFAST 0.20, LUNCH 0.25, DINNER 0.30, SNACK 0.15, SNACK 0.10.
List<MealAllocation> mealAllocationForFrequency(int frequency) {
  switch (frequency) {
    case 2:
      return const [
        MealAllocation(MealType.lunch, 0.50),
        MealAllocation(MealType.dinner, 0.50),
      ];
    case 3:
      return const [
        MealAllocation(MealType.breakfast, 0.30),
        MealAllocation(MealType.lunch, 0.35),
        MealAllocation(MealType.dinner, 0.35),
      ];
    case 4:
      return const [
        MealAllocation(MealType.breakfast, 0.25),
        MealAllocation(MealType.lunch, 0.30),
        MealAllocation(MealType.dinner, 0.30),
        MealAllocation(MealType.snack, 0.15),
      ];
    case 5:
      // Canonical order: BREAKFAST, SNACK, LUNCH, SNACK, DINNER (interleaved).
      return const [
        MealAllocation(MealType.breakfast, 0.20),
        MealAllocation(MealType.snack, 0.15),
        MealAllocation(MealType.lunch, 0.25),
        MealAllocation(MealType.snack, 0.10),
        MealAllocation(MealType.dinner, 0.30),
      ];
    default:
      return const [
        MealAllocation(MealType.breakfast, 0.30),
        MealAllocation(MealType.lunch, 0.35),
        MealAllocation(MealType.dinner, 0.35),
      ];
  }
}

class MealAllocation {
  const MealAllocation(this.mealType, this.fraction);
  final MealType mealType;
  final double fraction;
}

/// Default meal-name templates per meal type. 7 options each, cycled by day.
const Map<MealType, List<String>> defaultMealNames = {
  MealType.breakfast: [
    'Greek Yogurt Parfait',
    'Oatmeal Power Bowl',
    'Egg & Avocado Toast',
    'Protein Smoothie',
    'Cottage Cheese & Berries',
    'Banana Pancakes',
    'Breakfast Burrito',
  ],
  MealType.lunch: [
    'Chicken & Quinoa Bowl',
    'Tofu Stir-Fry',
    'Lentil Soup & Salad',
    'Turkey Wrap',
    'Salmon & Sweet Potato',
    'Beef Stir-Fry',
    'Mediterranean Bowl',
  ],
  MealType.dinner: [
    'Grilled Salmon',
    'Beef Stir-Fry',
    'Alicha Doro Wot',
    'Shiro Wot',
    'Roast Chicken',
    'Tofu Curry',
    'Lentil Stew',
  ],
  MealType.snack: [
    'Cottage Cheese & Berries',
    'Apple & Almonds',
    'Greek Yogurt',
    'Protein Shake',
    'Trail Mix',
    'Hummus & Veggies',
    'Boiled Eggs',
  ],
  MealType.side: [
    'Mixed Green Salad',
    'Roasted Vegetables',
    'Steamed Broccoli',
    'Quinoa Salad',
    'Sweet Potato Mash',
    'Coleslaw',
    'Garlic Bread',
  ],
  MealType.preWorkout: [
    'Banana Oats',
    'Oat Energy Bowl',
    'Apple & Peanut Butter',
    'Rice Cakes',
    'Smoothie',
    'Toast & Honey',
    'Dried Fruit Mix',
  ],
  MealType.postWorkout: [
    'Recovery Smoothie',
    'Greek Yogurt Bowl',
    'Protein Shake',
    'Chicken & Rice',
    'Tofu Bowl',
    'Chocolate Milk',
    'Egg & Avocado Toast',
  ],
};

/// Get the meal name for a (day, mealType) — cycles through 7 default options.
String mealNameFor(int dayNumber, MealType mealType) {
  final options = defaultMealNames[mealType] ?? ['Meal'];
  final idx = (dayNumber - 1) % options.length;
  return options[idx];
}

/// Training-day pattern by training-days-per-week. See §4.5 step 2.
/// 2d → [1, 4], 3d → [1, 3, 5], 4d → [1, 2, 4, 5],
/// 5d → [1, 2, 3, 4, 5], 6d → [1, 2, 3, 4, 5, 6].
List<int> trainingDaysFor(int daysPerWeek) {
  return switch (daysPerWeek) {
    2 => [1, 4],
    3 => [1, 3, 5],
    4 => [1, 2, 4, 5],
    5 => [1, 2, 3, 4, 5],
    6 => [1, 2, 3, 4, 5, 6],
    _ => [1, 3, 5],
  };
}
