/// Resting Metabolic Rate (RMR). See spec §4.3 step 1.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/nutrition.dart';
import '../models/assessment.dart';
import '../utils/round.dart';
import '../utils/units.dart';

/// Compute RMR.
///
/// - Formula: KATCH_MCARDLE if `bodyFatPct != null`, else MIFFLIN_ST_JEOR.
///   - Katch-McArdle throws if `bfPct ∉ [2, 60]` — caller catches and falls
///     back to Mifflin.
/// - Adjustments: × 0.95 if active deficit (cut/recomp); × 0.97 if
///   `weightReducedPct > 0.10`.
RMRResult computeRMR({
  required UserProfile profile,
  required CalorieStrategy strategy,
  required double weightReducedPct,
}) {
  final notes = <String>[];
  RMRFormula formula;
  double base;

  if (profile.bodyFatPct != null) {
    final bfPct = profile.bodyFatPct!;
    if (bfPct < 2 || bfPct > 60) {
      // Fall back to Mifflin per §11.17.
      formula = RMRFormula.mifflinStJeor;
      base = _mifflin(profile);
      notes.add(
          'Katch-McArdle unavailable (bfPct $bfPct out of [2,60]); fell back to Mifflin-St Jeor.');
    } else {
      formula = RMRFormula.katchMcArdle;
      final lbm = leanBodyMassKg(profile.weightKg, bfPct);
      base = 370 + 21.6 * lbm;
      notes.add('Katch-McArdle: 370 + 21.6 × ${round1(lbm)} kg LBM');
    }
  } else {
    // Try to use assessment-derived body fat if available.
    // (For standalone use, default to Mifflin.)
    formula = RMRFormula.mifflinStJeor;
    base = _mifflin(profile);
    notes.add('Mifflin-St Jeor (no body fat % available).');
  }

  var adaptationFactor = 1.0;
  if (strategy == CalorieStrategy.deficit ||
      strategy == CalorieStrategy.recomp) {
    adaptationFactor = 0.95;
    notes.add('Active-deficit metabolic adaptation ×0.95');
  }

  var weightReducedFactor = 1.0;
  if (weightReducedPct > 0.10) {
    weightReducedFactor = 0.97;
    notes.add(
        'Weight-reduced adaptation ×0.97 (reduced ${(weightReducedPct * 100).toStringAsFixed(1)}%)');
  }

  final adjusted = base * adaptationFactor * weightReducedFactor;
  return RMRResult(
    formula: formula,
    baseRmrKcal: round1(base),
    metabolicAdaptationFactor: adaptationFactor,
    weightReducedFactor: weightReducedFactor,
    adjustedRmrKcal: round1(adjusted),
    notes: notes,
  );
}

double _mifflin(UserProfile p) {
  // Mifflin: 10 × weight + 6.25 × height − 5 × age + (male ? 5 : -161)
  final sexTerm = p.sex == Sex.male ? 5.0 : -161.0;
  return 10 * p.weightKg + 6.25 * p.heightCm - 5 * p.age + sexTerm;
}

/// Variant that accepts an [AssessmentResult] (uses body comp BF% if user
/// didn't provide one). Useful for the full plan-generation pipeline.
RMRResult computeRMRWithAssessment({
  required UserProfile profile,
  required AssessmentResult assessment,
  required CalorieStrategy strategy,
  required double weightReducedPct,
}) {
  // Use assessment's body fat % if user didn't provide one.
  final profileWithBf = assessment.bodyComposition != null &&
          profile.bodyFatPct == null
      ? profile.copyWith(bodyFatPct: assessment.bodyComposition!.bodyFatPct)
      : profile;
  return computeRMR(
    profile: profileWithBf,
    strategy: strategy,
    weightReducedPct: weightReducedPct,
  );
}
