/// Micronutrient targets. See spec §4.3 step 7.
library;

import '../models/nutrition.dart';
import '../utils/round.dart';

/// Compute micronutrients.
///
/// - Fiber = 14 g × targetKcal / 1000
/// - Fruit/veg cups: 2/2 (≤2000 kcal), 3/3 (≤3000), 4/4 (>3000).
MicronutrientTargets computeMicronutrients({
  required double targetKcal,
}) {
  final notes = <String>[];
  final fiber = 14 * targetKcal / 1000;

  int fruitCups, vegCups;
  if (targetKcal <= 2000) {
    fruitCups = 2;
    vegCups = 2;
  } else if (targetKcal <= 3000) {
    fruitCups = 3;
    vegCups = 3;
  } else {
    fruitCups = 4;
    vegCups = 4;
  }

  notes.add('Fiber: 14 × ${targetKcal.round()} / 1000 = ${round1(fiber)} g');
  notes.add('Fruit/veg cups: $fruitCups/$vegCups');

  return MicronutrientTargets(
    fiberG: round1(fiber),
    fruitCups: fruitCups,
    vegCups: vegCups,
    notes: notes,
  );
}
