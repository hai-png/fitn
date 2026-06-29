/// Health risk sub-assessment. See spec §4.2.5, §9.3.
///
/// Computes WHR, WHtR, ABSI (with NHANES z-score), IBW (4 formulas),
/// and an overall weighted risk heuristic.
library;

import 'dart:math' as math;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/assessment.dart';
import '../utils/round.dart';
import '../utils/units.dart';

/// NHANES 1999-2004 ABSI age-band reference. See §9.3.
class _AbsiBand {
  const _AbsiBand(this.ageMin, this.ageMax, this.mean, this.sd);
  final int ageMin;
  final int ageMax;
  final double mean;
  final double sd;
}

const List<_AbsiBand> _maleBands = [
  _AbsiBand(18, 29, 0.0813, 0.0037),
  _AbsiBand(30, 39, 0.0815, 0.0038),
  _AbsiBand(40, 49, 0.0827, 0.0039),
  _AbsiBand(50, 59, 0.0846, 0.0042),
  _AbsiBand(60, 69, 0.0861, 0.0043),
  _AbsiBand(70, 999, 0.0874, 0.0045),
];

const List<_AbsiBand> _femaleBands = [
  _AbsiBand(18, 29, 0.0780, 0.0036),
  _AbsiBand(30, 39, 0.0779, 0.0037),
  _AbsiBand(40, 49, 0.0790, 0.0038),
  _AbsiBand(50, 59, 0.0821, 0.0041),
  _AbsiBand(60, 69, 0.0845, 0.0043),
  _AbsiBand(70, 999, 0.0867, 0.0045),
];

_AbsiBand _bandFor(int age, Sex sex) {
  final bands = sex == Sex.male ? _maleBands : _femaleBands;
  for (final b in bands) {
    if (age >= b.ageMin && age <= b.ageMax) return b;
  }
  return bands.last;
}

/// Classify ABSI z-score → risk. See §9.3.
ABSIRiskLevel _absiRiskFromZ(double z) {
  if (z < -0.868) return ABSIRiskLevel.low;
  if (z < -0.272) return ABSIRiskLevel.belowAverage;
  if (z < 0.229) return ABSIRiskLevel.average;
  if (z < 0.798) return ABSIRiskLevel.aboveAverage;
  return ABSIRiskLevel.high;
}

/// Classify WHR → risk. See §4.2.5.
HealthRiskLevel _whrRisk(double whr, Sex sex) {
  if (sex == Sex.male) {
    if (whr <= 0.85) return HealthRiskLevel.low;
    if (whr <= 0.90) return HealthRiskLevel.moderate;
    if (whr <= 1.0) return HealthRiskLevel.high;
    return HealthRiskLevel.veryHigh;
  } else {
    if (whr <= 0.80) return HealthRiskLevel.low;
    if (whr <= 0.85) return HealthRiskLevel.moderate;
    if (whr <= 1.0) return HealthRiskLevel.high;
    return HealthRiskLevel.veryHigh;
  }
}

/// Classify WHtR → risk. See §4.2.5.
HealthRiskLevel _whtrRisk(double whtr, Sex sex) {
  if (sex == Sex.male) {
    if (whtr < 0.50) return HealthRiskLevel.low;
    if (whtr < 0.53) return HealthRiskLevel.moderate;
    if (whtr < 0.58) return HealthRiskLevel.high;
    return HealthRiskLevel.veryHigh;
  } else {
    if (whtr < 0.46) return HealthRiskLevel.low;
    if (whtr < 0.49) return HealthRiskLevel.moderate;
    if (whtr < 0.54) return HealthRiskLevel.high;
    return HealthRiskLevel.veryHigh;
  }
}

/// Ideal Body Weight (4 formulas). See §4.2.5.
class _Ibw {
  _Ibw(this.devine, this.robinson, this.miller, this.hamwi);
  final double devine;
  final double robinson;
  final double miller;
  final double hamwi;
}

_Ibw _computeIbw(double heightCm, Sex sex) {
  final heightIn = heightCm * cmToIn;
  final inchesOver60 = (heightIn - 60).clamp(0.0, double.infinity);
  if (sex == Sex.male) {
    return _Ibw(
      50 + 2.3 * inchesOver60,
      52 + 1.9 * inchesOver60,
      56.2 + 1.41 * inchesOver60,
      48 + 2.7 * inchesOver60,
    );
  } else {
    return _Ibw(
      45.5 + 2.3 * inchesOver60,
      49 + 1.7 * inchesOver60,
      53.1 + 1.36 * inchesOver60,
      45.4 + 2.2 * inchesOver60,
    );
  }
}

/// Weighted overall risk heuristic. See §4.2.5.
///
/// ABSI weight 0.5, WHR 0.3, WHtR 0.2. Add weight when metric is HIGH/VERY_HIGH
/// (ABSI: ABOVE_AVERAGE/HIGH). Map: ≥0.75 → VERY_HIGH, ≥0.50 → HIGH, any
/// clinical risk factor → MODERATE, else LOW.
HealthRiskLevel _overallRisk(
    HealthRiskLevel? whrRisk,
    HealthRiskLevel? whtrRisk,
    ABSIRiskLevel? absiRisk,
    List<String> riskFactors) {
  double score = 0;
  if (absiRisk != null) {
    double absiScore;
    switch (absiRisk) {
      case ABSIRiskLevel.low:
        absiScore = 0.0;
      case ABSIRiskLevel.belowAverage:
        absiScore = 0.1;
      case ABSIRiskLevel.average:
        absiScore = 0.3;
      case ABSIRiskLevel.aboveAverage:
        absiScore = 0.6;
      case ABSIRiskLevel.high:
        absiScore = 0.9;
    }
    score += 0.5 * absiScore;
  }
  if (whrRisk != null) {
    double whrScore;
    switch (whrRisk) {
      case HealthRiskLevel.low:
        whrScore = 0.0;
      case HealthRiskLevel.moderate:
        whrScore = 0.2;
      case HealthRiskLevel.high:
        whrScore = 0.6;
      case HealthRiskLevel.veryHigh:
        whrScore = 0.9;
    }
    score += 0.3 * whrScore;
  }
  if (whtrRisk != null) {
    double whtrScore;
    switch (whtrRisk) {
      case HealthRiskLevel.low:
        whtrScore = 0.0;
      case HealthRiskLevel.moderate:
        whtrScore = 0.2;
      case HealthRiskLevel.high:
        whtrScore = 0.6;
      case HealthRiskLevel.veryHigh:
        whtrScore = 0.9;
    }
    score += 0.2 * whtrScore;
  }

  if (score >= 0.75) return HealthRiskLevel.veryHigh;
  if (score >= 0.50) return HealthRiskLevel.high;
  if (riskFactors.isNotEmpty) return HealthRiskLevel.moderate;
  return HealthRiskLevel.low;
}

/// Run the health risk sub-assessment.
///
/// Returns null when no circumference measurements are available (WHR/WHtR/
/// ABSI all require waist + hip).
HealthRiskAssessment? assessHealthRisk(UserProfile profile) {
  try {
    final waistCm = profile.waistCm;
    final hipCm = profile.hipCm;
    final neckCm = profile.neckCm;
    final heightM = profile.heightM;

    if (waistCm == null) return null;

    // WHR requires hip.
    double? whr;
    HealthRiskLevel? whrLvl;
    if (hipCm != null && hipCm > 0) {
      whr = waistCm / hipCm;
      whrLvl = _whrRisk(whr, profile.sex);
    }

    // WHtR requires only waist.
    final whtr = waistCm / profile.heightCm;
    final whtrLvl = _whtrRisk(whtr, profile.sex);

    // ABSI requires waist, weight, height.
    double? absi;
    double? absiZ;
    ABSIRiskLevel? absiLvl;
    if (hipCm != null || profile.sex == Sex.male) {
      // ABSI: (waist_m) × weight^(-2/3) × height^(5/6)
      final waistM = waistCm / 100;
      absi = waistM *
          math.pow(profile.weightKg, -2 / 3) *
          math.pow(profile.heightCm, 5 / 6);
      final band = _bandFor(profile.age, profile.sex);
      absiZ = (absi - band.mean) / band.sd;
      absiLvl = _absiRiskFromZ(absiZ);
    }

    final ibw = _computeIbw(profile.heightCm, profile.sex);

    final riskFactors = <String>[];
    if (whrLvl == HealthRiskLevel.high ||
        whrLvl == HealthRiskLevel.veryHigh) {
      riskFactors.add('elevated WHR');
    }
    if (whtrLvl == HealthRiskLevel.high ||
        whtrLvl == HealthRiskLevel.veryHigh) {
      riskFactors.add('elevated WHtR');
    }
    if (absiLvl == ABSIRiskLevel.aboveAverage ||
        absiLvl == ABSIRiskLevel.high) {
      riskFactors.add('elevated ABSI');
    }

    final overall = _overallRisk(whrLvl, whtrLvl, absiLvl, riskFactors);

    final notes = <String>[];
    if (whr != null) notes.add('WHR ${round2(whr)} (${whrLvl!.display})');
    notes.add('WHtR ${round2(whtr)} (${whtrLvl.display})');
    if (absi != null) {
      notes.add(
          'ABSI ${round4(absi)} (z=${round2(absiZ!)}, ${absiLvl!.display})');
    }
    notes.add('IBW Devine ${round1(ibw.devine)} kg');

    return HealthRiskAssessment(
      whr: whr != null ? round2(whr) : null,
      whrRisk: whrLvl,
      whtr: round2(whtr),
      whtrRisk: whtrLvl,
      absi: absi != null ? round4(absi) : null,
      absiZScore: absiZ != null ? round2(absiZ) : null,
      absiRisk: absiLvl,
      ibwDevineKg: round1(ibw.devine),
      ibwRobinsonKg: round1(ibw.robinson),
      ibwMillerKg: round1(ibw.miller),
      ibwHamwiKg: round1(ibw.hamwi),
      overallRisk: overall,
      riskFactors: riskFactors,
      notes: notes,
    );
  } catch (_) {
    return null;
  }
}

double round4(double v) => _round4(v);
double _round4(double v) {
  // Simple 4-decimal banker's-style rounding.
  return (v * 10000).roundToDouble() / 10000;
}
