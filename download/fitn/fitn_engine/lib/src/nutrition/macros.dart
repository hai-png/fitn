/// Macro split. See spec §4.3 step 5.
library;

import 'dart:math';

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/nutrition.dart';
import '../utils/round.dart';
import '../utils/units.dart';
import '../assessment/thresholds.dart';

/// Compute macros.
///
/// - Protein:
///   - Obese override (bfPct >= obese_threshold): `1g × heightCm`.
///   - BF% known: `lbm_lb × 1.14` (cut) or `× 1.0` (else).
///   - BF% unknown: `target_weight_lb × 1.0` (cut, target = 90% current) or
///     `weight_lb × 0.73` (else).
///   - Diet boost: vegan ×1.20 (ceil), vegetarian ×1.10 (ceil).
/// - Fat: midpoint of strategy range (deficit/recomp 15-25%;
///   surplus/maintenance/reverse 20-30%). Floor: max(40, weight_lb × 0.25).
///   Saturated ceiling: 10% of calories.
/// - Carbs: remainder = targetKcal − proteinKcal − fatKcal, clamped ≥0.
MacroSplit computeMacros({
  required UserProfile profile,
  required CalorieStrategy strategy,
  required double targetKcal,
  required double bodyFatPct, // may be from assessment
}) {
  final notes = <String>[];
  final b = sexBoundaries(profile.sex);
  final isObese = bodyFatPct >= b.obeseThreshold;
  final isCut = strategy == CalorieStrategy.deficit ||
      strategy == CalorieStrategy.recomp;

  // === Protein ===
  double proteinG;
  if (isObese) {
    proteinG = proteinGPerCmHeightObese * profile.heightCm;
    notes.add(
        'Protein: obese override 1g × ${profile.heightCm}cm = ${round1(proteinG)}g');
  } else {
    final lbm = leanBodyMassKg(profile.weightKg, bodyFatPct);
    final lbm_lb = lbm * kgToLb;
    if (isCut) {
      proteinG = lbm_lb * proteinPerLbLbmCut;
      notes.add(
          'Protein: cut ${proteinPerLbLbmCut} g/lb LBM × ${round1(lbm_lb)} lb = ${round1(proteinG)}g');
    } else {
      proteinG = lbm_lb * proteinPerLbLbmNonCut;
      notes.add(
          'Protein: non-cut ${proteinPerLbLbmNonCut} g/lb LBM × ${round1(lbm_lb)} lb = ${round1(proteinG)}g');
    }
  }

  // Diet boost.
  if (profile.dietType == DietType.vegan) {
    proteinG = (proteinG * veganProteinBoost).ceilToDouble();
    notes.add('Vegan protein boost ×$veganProteinBoost (ceil) → ${round1(proteinG)}g');
  } else if (profile.dietType == DietType.vegetarian) {
    proteinG = (proteinG * vegetarianProteinBoost).ceilToDouble();
    notes.add('Vegetarian protein boost ×$vegetarianProteinBoost (ceil) → ${round1(proteinG)}g');
  }

  // === Fat ===
  final fatPctRange = (isCut)
      ? (const Range(0.15, 0.25))
      : (const Range(0.20, 0.30));
  final fatPctTarget = (fatPctRange.min + fatPctRange.max) / 2;
  var fatKcalFromPct = targetKcal * fatPctTarget;
  var fatG = fatKcalFromPct / kcalPerGramFat;

  // Floor: max(40, weight_lb × 0.25).
  final weightLb = profile.weightLb;
  final fatFloor = max(fatAbsoluteFloorG.toDouble(), weightLb * fatPerLbFloor);
  if (fatG < fatFloor) {
    fatG = fatFloor;
    notes.add('Fat floor applied: ${round1(fatFloor)}g');
  } else {
    notes.add(
        'Fat: ${fatPctRange.min * 100}-${fatPctRange.max * 100}% midpoint (${(fatPctTarget * 100).toStringAsFixed(1)}%) → ${round1(fatG)}g');
  }

  // === Carbs ===
  final proteinKcal = proteinG * kcalPerGramProtein;
  final fatKcal = fatG * kcalPerGramFat;
  final carbKcal = max(0.0, targetKcal - proteinKcal - fatKcal);
  final carbG = carbKcal / kcalPerGramCarb;
  notes.add(
      'Carbs: remainder = ${round1(targetKcal)} − ${round1(proteinKcal)} (P) − ${round1(fatKcal)} (F) = ${round1(carbKcal)} kcal → ${round1(carbG)}g');

  // === Percentages ===
  final proteinPct = (proteinKcal / targetKcal) * 100;
  final fatPct = (fatKcal / targetKcal) * 100;
  final carbPct = (carbKcal / targetKcal) * 100;

  return MacroSplit(
    proteinG: round1(proteinG),
    fatG: round1(fatG),
    carbG: round1(carbG),
    proteinPct: round1(proteinPct),
    fatPct: round1(fatPct),
    carbPct: round1(carbPct),
    proteinKcal: round1(proteinKcal),
    fatKcal: round1(fatKcal),
    carbKcal: round1(carbKcal),
    notes: notes,
  );
}

class Range {
  const Range(this.min, this.max);
  final double min;
  final double max;
}
