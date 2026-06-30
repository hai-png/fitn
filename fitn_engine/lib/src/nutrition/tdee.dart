/// Total Daily Energy Expenditure (TDEE). See spec §4.3 step 2-3.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/nutrition.dart';
import '../utils/round.dart';
import '../utils/units.dart';

/// Compute TDEE.
///
/// - RippedBody activity factors (1.25 / 1.45 / 1.65 / 1.85 / 2.05).
/// - Adaptive TDEE: requires `weightLogKg` and `intakeLogKcal` to be both
///   non-empty, equal-length, and ≥8 entries.
///   - `observed = avgIntake − (Δweight × 7700) / nDays`
///   - Sanity: `observed ∈ [800, 7000]`, else skip.
///   - Ramp weight: `w = clamp((nDays − 7) / 53, 0, 1)` — no adaptation below
///     7 days, full at 60+.
///   - `adaptive = w × observed + (1 − w) × tdee`.
TDEEResult computeTDEE({
  required double rmrKcal,
  required ActivityLevel activityLevel,
  required List<double> weightLogKg,
  required List<double> intakeLogKcal,
}) {
  final notes = <String>[];
  final activityFactor = activityLevel.activityFactor;
  final tdee = rmrKcal * activityFactor;
  notes.add(
      'RMR ${round1(rmrKcal)} × activity ${activityFactor} = ${round1(tdee)} kcal');

  double? adaptive;
  if (weightLogKg.isNotEmpty &&
      intakeLogKcal.isNotEmpty &&
      weightLogKg.length == intakeLogKcal.length &&
      weightLogKg.length >= 8) {
    final nDays = weightLogKg.length;
    final avgIntake = intakeLogKcal.reduce((a, b) => a + b) / nDays;
    final dWeight = weightLogKg.last - weightLogKg.first;
    final observed = avgIntake - (dWeight * kcalPerKgFat) / nDays;
    if (observed >= 800 && observed <= 7000) {
      final w = ((nDays - 7) / 53).clamp(0.0, 1.0);
      adaptive = w * observed + (1 - w) * tdee;
      notes.add(
          'Adaptive TDEE: ramp ${(w * 100).toStringAsFixed(0)}%, observed ${round1(observed)} → blended ${round1(adaptive)} kcal');
    } else {
      notes.add(
          'Adaptive TDEE skipped: observed ${round1(observed)} outside [800,7000]');
    }
  } else {
    if (weightLogKg.isNotEmpty || intakeLogKcal.isNotEmpty) {
      notes.add(
          'Adaptive TDEE skipped: logs not equal-length or <8 entries');
    }
  }

  final finalTdee = adaptive ?? tdee;
  return TDEEResult(
    rmrKcal: round1(rmrKcal),
    activityFactor: activityFactor,
    tdeeKcal: round1(tdee),
    adaptiveTdeeKcal: adaptive != null ? round1(adaptive) : null,
    finalTdeeKcal: round1(finalTdee),
    notes: notes,
  );
}
