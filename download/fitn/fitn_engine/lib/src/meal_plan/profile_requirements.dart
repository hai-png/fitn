import 'package:fitn_engine/src/models/enums.dart';
import 'package:fitn_engine/src/meal_plan/meal_templates.dart';
import 'package:fitn_engine/src/meal_plan/recipe_scorer.dart';
import 'package:fitn_engine/src/models/nutrition.dart';
import 'package:fitn_engine/src/utils/round.dart';

/// Compute slot targets from daily macros × meal allocation.
/// Spec §4.5 step 1.
class SlotAllocation {
  final MealType mealType;
  final double fraction;
  const SlotAllocation(this.mealType, this.fraction);
}

/// Allocation tables. Spec §4.5 step 1.
List<SlotAllocation> slotAllocationsFor(int mealFrequency) {
  return switch (mealFrequency) {
    2 => const [
        SlotAllocation(MealType.lunch, 0.50),
        SlotAllocation(MealType.dinner, 0.50),
      ],
    3 => const [
        SlotAllocation(MealType.breakfast, 0.30),
        SlotAllocation(MealType.lunch, 0.35),
        SlotAllocation(MealType.dinner, 0.35),
      ],
    4 => const [
        SlotAllocation(MealType.breakfast, 0.25),
        SlotAllocation(MealType.lunch, 0.30),
        SlotAllocation(MealType.dinner, 0.30),
        SlotAllocation(MealType.snack, 0.15),
      ],
    5 => const [
        SlotAllocation(MealType.breakfast, 0.20),
        SlotAllocation(MealType.lunch, 0.25),
        SlotAllocation(MealType.dinner, 0.30),
        SlotAllocation(MealType.snack, 0.15),
        SlotAllocation(MealType.snack, 0.10),
      ],
    6 => const [
        SlotAllocation(MealType.breakfast, 0.20),
        SlotAllocation(MealType.lunch, 0.20),
        SlotAllocation(MealType.dinner, 0.25),
        SlotAllocation(MealType.snack, 0.15),
        SlotAllocation(MealType.snack, 0.10),
        SlotAllocation(MealType.snack, 0.10),
      ],
    _ => const [
        SlotAllocation(MealType.breakfast, 0.30),
        SlotAllocation(MealType.lunch, 0.35),
        SlotAllocation(MealType.dinner, 0.35),
      ],
  };
}

/// Compute the per-slot target macros.
List<SlotTarget> computeSlotTargets({
  required int mealFrequency,
  required MacroSplit macros,
}) {
  final allocs = slotAllocationsFor(mealFrequency);
  return allocs
      .map((a) => SlotTarget(
            kcal: roundBankers(macros.proteinKcal + macros.fatKcal + macros.carbKcal, 1) * a.fraction,
            proteinG: roundBankers(macros.proteinG * a.fraction, 1),
            carbG: roundBankers(macros.carbG * a.fraction, 1),
            fatG: roundBankers(macros.fatG * a.fraction, 1),
            fiberG: 0,
          ))
      .toList();
}

/// Determine training days for the 7-day week. Spec §4.5 step 2.
List<int> trainingDaysFor(int trainingDaysPerWeek) {
  return switch (trainingDaysPerWeek) {
    2 => const [1, 4],
    3 => const [1, 3, 5],
    4 => const [1, 2, 4, 5],
    5 => const [1, 2, 3, 4, 5],
    6 => const [1, 2, 3, 4, 5, 6],
    _ => const [1, 3, 5],
  };
}

/// Derive the diet tag from the user's diet type.
/// Spec §4.5: vegetarian → VEGAN (recipe DB has no separate vegetarian tag).
String dietTagFor(DietType dietType) {
  return switch (dietType) {
    DietType.omnivore => 'OMNI',
    DietType.vegan => 'VEGAN',
    DietType.vegetarian => 'VEGAN', // spec §11.2
  };
}

/// Map goal to a recipe goal_fit tag string.
String? goalFitTagFor(String trainingGoalName) {
  return switch (trainingGoalName) {
    'fatLoss' || 'fat_loss' => 'cut',
    'muscleGain' || 'muscle_gain' => 'bulk',
    'recomp' => 'recomp',
    'maintenance' => 'maintenance',
    'strength' => 'strength',
    _ => null,
  };
}
