/// Body composition sub-assessment. See spec §4.2.1, §4.2.4.
///
/// Implements the 3-method body fat priority order:
/// 1. User-provided body fat %.
/// 2. US Navy circumference (Hodgdon & Beckett 1984), if measurements present.
/// 3. CUN-BAE (always computable).
library;

import 'dart:math' as math;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/assessment.dart';
import '../utils/round.dart';
import '../utils/units.dart';
import 'categories.dart';
import 'constants.dart';

/// Result of the BF% selection (priority order).
class _BfSelection {
  _BfSelection(this.bodyFatPct, this.method);
  final double bodyFatPct;
  final BodyFatMethod method;
}

/// Pick body fat % using the priority order in §4.2.1.
_BfSelection? _selectBodyFatPct(UserProfile p) {
  // 1. User-provided.
  if (p.bodyFatPct != null) {
    final clamped = clampDouble(p.bodyFatPct!, 2.0, 60.0);
    return _BfSelection(clamped, BodyFatMethod.userProvided);
  }

  // 2. US Navy circumference (Hodgdon & Beckett 1984).
  if (p.hasCircumferenceMeasurements) {
    final navyBf = _navyBodyFat(p);
    if (navyBf != null) {
      return _BfSelection(clampDouble(navyBf, 2.0, 60.0), BodyFatMethod.navy);
    }
  }

  // 3. CUN-BAE (always computable).
  final cunBae = _cunBaeBodyFat(p);
  return _BfSelection(clampDouble(cunBae, 2.0, 60.0), BodyFatMethod.cunBae);
}

/// US Navy circumference body fat formula (Hodgdon & Beckett 1984). See §4.2.1.
double? _navyBodyFat(UserProfile p) {
  final heightIn = p.heightIn;
  final waistIn = p.waistCm! * cmToIn;
  final neckIn = p.neckCm! * cmToIn;
  if (p.sex == Sex.male) {
    final diff = waistIn - neckIn;
    if (diff <= 0) return null;
    final bf = 86.010 * log10(diff) - 70.041 * log10(heightIn) + 36.76;
    return bf;
  } else {
    final hipIn = (p.hipCm ?? 0) * cmToIn;
    final diff = waistIn + hipIn - neckIn;
    if (diff <= 0) return null;
    final bf =
        163.205 * log10(diff) - 97.684 * log10(heightIn) - 78.387;
    return bf;
  }
}

/// CUN-BAE body fat formula (always computable). See §4.2.1.
///
/// Note: coefficient is 1.0689, NOT the published-paper typo 1.39. See §11.15.
double _cunBaeBodyFat(UserProfile p) {
  final bmi = p.bmi;
  final sexTerm = p.sex == Sex.female ? 1.0 : 0.0;
  // bf = -24.988 + 0.503 × age + 1.0689 × bmi + 0.462 × sexTerm
  final bf = -24.988 + 0.503 * p.age + 1.0689 * bmi + 0.462 * sexTerm;
  return bf;
}

/// Compute the FFMI and normalized FFMI per §4.2.4.
class _FfmiResult {
  _FfmiResult(this.ffmi, this.normalizedFfmi);
  final double ffmi;
  final double normalizedFfmi;
}

_FfmiResult _computeFfmi(double weightKg, double bfPct, double heightM) {
  final ffmKg = weightKg * (1 - bfPct / 100);
  final ffmi = ffmKg / (heightM * heightM);
  final normalizedFfmi =
      ffmi + ffmiNormalizationCoef * (ffmiReferenceHeightM - heightM);
  return _FfmiResult(ffmi, normalizedFfmi);
}

/// Compute target weights (kg) at named BF% landmarks.
///
/// `targetWeight = lbm / (1 − targetBf/100)` where
/// `lbm = currentWeight × (1 − currentBf/100)`.
Map<String, double> _targetWeightsKg(
    double currentWeightKg, double currentBfPct, Sex sex) {
  final lbm = currentWeightKg * (1 - currentBfPct / 100);
  final targets = namedBfTargets(sex);
  return {
    'athletic': round1(_targetAt(lbm, targets.athletic)),
    'fitness': round1(_targetAt(lbm, targets.fitness)),
    'acceptable': round1(_targetAt(lbm, targets.acceptable)),
    'hormonal_floor': round1(_targetAt(lbm, targets.hormonalFloor)),
  };
}

double _targetAt(double lbm, double targetBf) {
  final denom = 1 - targetBf / 100;
  if (denom <= 0) return double.infinity;
  return lbm / denom;
}

/// Run the body composition sub-assessment.
///
/// Returns null only if [UserProfile.bodyFatPct] is invalid (out of [2, 60]) —
/// the 3-method priority order otherwise always produces a result.
BodyComposition? assessBodyComposition(UserProfile profile) {
  try {
    final selection = _selectBodyFatPct(profile);
    if (selection == null) return null;

    final bfPct = selection.bodyFatPct;
    final lbm = leanBodyMassKg(profile.weightKg, bfPct);
    final fm = fatMassKg(profile.weightKg, bfPct);
    final bmiVal = profile.bmi;
    final ffmi = _computeFfmi(profile.weightKg, bfPct, profile.heightM);

    final targets = _targetWeightsKg(profile.weightKg, bfPct, profile.sex);

    final notes = <String>[];
    notes.add('Body fat method: ${selection.method.display}');
    notes.add(
        'Lean mass ${round1(lbm)} kg, fat mass ${round1(fm)} kg');
    notes.add(
        'FFMI ${round1(ffmi.ffmi)}, normalized ${round1(ffmi.normalizedFfmi)}');

    return BodyComposition(
      bodyFatPct: round1(bfPct),
      bodyFatMethod: selection.method,
      bodyFatCategory: bodyFatCategory(bfPct, profile.sex),
      leanBodyMassKg: round1(lbm),
      fatMassKg: round1(fm),
      bmi: round1(bmiVal),
      bmiCategory: bmiCategory(bmiVal),
      ffmi: round1(ffmi.ffmi),
      normalizedFfmi: round1(ffmi.normalizedFfmi),
      targetWeightsKg: targets,
      notes: notes,
    );
  } catch (e) {
    return null;
  }
}
