/// Hydration target. See spec §4.3 step 6 + §9.10.
///
/// Multi-step FatCalc:
/// - Base: weightKg × 0.030 L
/// - Sex: +0.3 L (male)
/// - Exercise: hours × sweatRate / 1000 (light 300, moderate 500, intense 800
///   mL/hr)
/// - Climate multiplier (cold 0.95, temperate 1.0, hot 1.3, hot_humid 1.4)
///   applied to exercise component only
/// - Pregnancy +0.3 L, breastfeeding +0.7 L (throws if male — engine catches)
/// - Soft ceiling 5.0 L (hyponatremia protection)
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/nutrition.dart';
import '../utils/round.dart';

/// Compute hydration.
///
/// [isPregnant] and [isBreastfeeding] default to false; both throw if true on
/// a male profile (the engine catches and falls back to non-pregnancy).
HydrationTarget computeHydration({
  required UserProfile profile,
  required double exerciseHoursPerDay,
  required ExerciseIntensity exerciseIntensity,
  required Climate climate,
  bool isPregnant = false,
  bool isBreastfeeding = false,
}) {
  final notes = <String>[];
  final components = <String, double>{};

  // Base.
  final baseL = profile.weightKg * 0.030;
  components['base'] = round2(baseL);
  notes.add('Base: ${profile.weightKg} kg × 0.030 = ${round2(baseL)} L');

  // Sex addition.
  var total = baseL;
  if (profile.sex == Sex.male) {
    total += 0.3;
    components['sex_male'] = 0.3;
    notes.add('Male +0.3 L');
  }

  // Exercise component.
  final sweatMlPerHour = exerciseIntensity.sweatRateMlPerHour;
  final exerciseL = exerciseHoursPerDay * sweatMlPerHour / 1000;
  final climateMult = climate.multiplier;
  final exerciseLAdjusted = exerciseL * climateMult;
  total += exerciseLAdjusted;
  components['exercise'] = round2(exerciseLAdjusted);
  notes.add(
      'Exercise: ${exerciseHoursPerDay}h × ${sweatMlPerHour} mL/hr × ${climateMult} = ${round2(exerciseLAdjusted)} L');

  // Pregnancy / breastfeeding.
  if (isPregnant) {
    if (profile.sex == Sex.male) {
      throw ArgumentError('Pregnancy not applicable to male profile');
    }
    total += 0.3;
    components['pregnancy'] = 0.3;
    notes.add('Pregnancy +0.3 L');
  }
  if (isBreastfeeding) {
    if (profile.sex == Sex.male) {
      throw ArgumentError('Breastfeeding not applicable to male profile');
    }
    total += 0.7;
    components['breastfeeding'] = 0.7;
    notes.add('Breastfeeding +0.7 L');
  }

  // Soft ceiling 5.0 L.
  if (total > hydrationSoftCeilingL) {
    notes.add(
        'Soft ceiling applied: ${round2(total)} L → $hydrationSoftCeilingL L');
    total = hydrationSoftCeilingL;
  }

  return HydrationTarget(
    waterLitersPerDay: round2(total),
    components: components,
    notes: notes,
  );
}
