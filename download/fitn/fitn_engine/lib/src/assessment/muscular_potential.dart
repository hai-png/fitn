/// Muscular potential sub-assessment. See spec §4.2.6.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/assessment.dart';
import '../utils/round.dart';
import '../utils/units.dart';
import 'constants.dart';

/// Run the muscular potential sub-assessment.
///
/// Requires a body fat percentage (skipped if body composition is null).
MuscularPotential? assessMuscularPotential(
    UserProfile profile, double bodyFatPct) {
  try {
    final ffmKg = profile.weightKg * (1 - bodyFatPct / 100);
    final heightM = profile.heightM;
    final ffmi = ffmKg / (heightM * heightM);
    final normalizedFfmi =
        ffmi + ffmiNormalizationCoef * (ffmiReferenceHeightM - heightM);

    final ceilingPct = (normalizedFfmi / ffmiNaturalCommon * 100).clamp(0, 100);

    // FFM at ceiling: (ceiling - 6.1 × (1.8 - height)) × height^2.
    final ffmAtCeiling =
        (ffmiNaturalCommon - ffmiNormalizationCoef * (ffmiReferenceHeightM - heightM)) *
            heightM * heightM;
    final headroomKg = (ffmAtCeiling - ffmKg).clamp(0.0, double.infinity);

    // Berkhan stage max (men only): heightCm − 100 at 5-6% BF.
    final berkhanMax = profile.sex == Sex.male
        ? (profile.heightCm - 100).toDouble()
        : null;

    // Expected monthly muscle gain (men; ×0.5 for women).
    final monthlyGainMen = monthlyMuscleGainKgMen[profile.trainingStatus]!;
    final monthlyGain =
        profile.sex == Sex.male ? monthlyGainMen : monthlyGainMen * 0.5;

    final isAboveCeiling = normalizedFfmi > ffmiNaturalCommon;

    final notes = <String>[];
    notes.add(
        'Normalized FFMI ${round1(normalizedFfmi)} vs natural ceiling ${ffmiNaturalCommon}');
    notes.add('Headroom ${round1(headroomKg)} kg lean mass');
    notes.add(
        'Expected monthly muscle gain: ${round2(monthlyGain)} kg');
    if (berkhanMax != null) {
      notes.add('Berkhan stage max: ${round1(berkhanMax)} kg at 5–6% BF');
    }

    return MuscularPotential(
      currentFfmi: round1(ffmi),
      currentNormalizedFfmi: round1(normalizedFfmi),
      naturalCeilingFfmi: ffmiNaturalCommon,
      attainableCeilingFfmi: ffmiAttainable,
      likelyMaxFfmi: ffmiLikelyMax,
      berkhanStageMaxKg: berkhanMax != null ? round1(berkhanMax) : null,
      ffmiToCeilingPct: round1(ceilingPct.toDouble()),
      headroomKg: round1(headroomKg),
      expectedMonthlyMuscleGainKg: round2(monthlyGain),
      isAboveCeiling: isAboveCeiling,
      notes: notes,
    );
  } catch (_) {
    return null;
  }
}
