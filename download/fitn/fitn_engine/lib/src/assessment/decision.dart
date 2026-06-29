/// Strategy decision tree. See spec §4.2.7.
///
/// Implements the first-match-wins algorithm using sex-specific boundaries
/// from `thresholds.dart`. Also produces a human-readable rationale string.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import 'thresholds.dart';

class _StrategyDecision {
  _StrategyDecision(this.strategy, this.rationale);
  final RecommendedStrategy strategy;
  final String rationale;
}

/// Compute the recommended strategy + rationale.
_StrategyDecision _decide(UserProfile p, double bfPct) {
  final b = sexBoundaries(p.sex);

  // 1. Safety override (obesity).
  if (bfPct >= b.obeseThreshold) {
    if (p.trainingStatus == TrainingStatus.beginner &&
        p.primaryGoal != PrimaryGoal.fatLoss) {
      return _StrategyDecision(
        RecommendedStrategy.habitChangeFirst,
        'Body fat is in the obesity range and you are a beginner — start with habit changes before calorie counting.',
      );
    }
    return _StrategyDecision(
      RecommendedStrategy.cut,
      'Body fat is in the obesity range — prioritise fat loss.',
    );
  }

  // 2. Goal = maintenance.
  if (p.primaryGoal == PrimaryGoal.maintenance) {
    if (bfPct < b.hormonalFloor()) {
      return _StrategyDecision(
        RecommendedStrategy.maintenance,
        'Body fat is below the hormonal floor — consider bulking instead.',
      );
    }
    if (bfPct > b.operationalHi) {
      return _StrategyDecision(
        RecommendedStrategy.maintenance,
        'Body fat is above the operational window — consider cutting instead.',
      );
    }
    // Reverse-diet detection.
    if (p.intakeLogKcal.length >= 30 &&
        bfPct >= b.operationalLo &&
        bfPct <= b.operationalHi) {
      // Trailing 7-day avg intake vs estimated TDEE.
      final recentIntake =
          p.intakeLogKcal.sublist(p.intakeLogKcal.length - 7).reduce((a, b) => a + b) /
              7;
      final estimatedTdee = p.weightKg * 35; // crude fallback
      if (recentIntake < estimatedTdee * 0.90) {
        return _StrategyDecision(
          RecommendedStrategy.reverseDiet,
          'Recent intake is well below estimated TDEE — reverse-diet to restore metabolic rate.',
        );
      }
    }
    return _StrategyDecision(
      RecommendedStrategy.maintenance,
      'Maintenance is appropriate at your current body fat.',
    );
  }

  // 3. Goal = strength.
  if (p.primaryGoal == PrimaryGoal.strength) {
    if (bfPct > b.bulkCeiling) {
      return _StrategyDecision(
        RecommendedStrategy.cut,
        'Body fat is above the bulk ceiling — cut first to make room for a strength bulk.',
      );
    }
    return _StrategyDecision(
      RecommendedStrategy.maintenance,
      'Maintenance is appropriate for strength at your current body fat.',
    );
  }

  // 4. Goal = fat_loss.
  if (p.primaryGoal == PrimaryGoal.fatLoss) {
    if (bfPct < b.cutFloor) {
      return _StrategyDecision(
        RecommendedStrategy.maintenance,
        'Body fat is below the cut floor — protect hormones, run maintenance instead.',
      );
    }
    return _StrategyDecision(
      RecommendedStrategy.cut,
      'Cutting is appropriate for your fat-loss goal at ${bfPct.toStringAsFixed(1)}% body fat.',
    );
  }

  // 5. Goal = muscle_gain.
  if (p.primaryGoal == PrimaryGoal.muscleGain) {
    if (bfPct > b.bulkCeiling) {
      return _StrategyDecision(
        RecommendedStrategy.cut,
        'Body fat is above the bulk ceiling — cut first to make room for a clean bulk.',
      );
    }
    return _StrategyDecision(
      RecommendedStrategy.bulk,
      'Bulking is appropriate for your muscle-gain goal.',
    );
  }

  // 6. Goal = recomp.
  if (p.primaryGoal == PrimaryGoal.recomp) {
    if (bfPct >= b.recompExcellent) {
      return _StrategyDecision(
        RecommendedStrategy.recomp,
        'Recomp potential is excellent at your body fat.',
      );
    }
    if (bfPct >= b.recompGoodLo) {
      return _StrategyDecision(
        RecommendedStrategy.recomp,
        'Recomp potential is good at your body fat.',
      );
    }
    return _StrategyDecision(
      RecommendedStrategy.bulk,
      'Recomp potential is limited at your body fat — bulk to build muscle.',
    );
  }

  // 7. Auto-decide (no explicit goal override — fallback path).
  // (Reached only if primaryGoal was somehow not in the enum above.)
  if (bfPct > b.operationalHi) {
    return _StrategyDecision(
      RecommendedStrategy.cut,
      'Auto-decided: body fat above operational window.',
    );
  }
  if (bfPct < b.cutFloor) {
    return _StrategyDecision(
      RecommendedStrategy.bulk,
      'Auto-decided: body fat below cut floor.',
    );
  }
  if (p.trainingStatus == TrainingStatus.novice &&
      bfPct >= b.skinnyFatLo &&
      bfPct <= b.skinnyFatHi) {
    return _StrategyDecision(
      RecommendedStrategy.recomp,
      'Auto-decided: novice + skinny-fat range — recomp.',
    );
  }
  if (p.trainingStatus == TrainingStatus.novice && bfPct < b.bulkStart) {
    return _StrategyDecision(
      RecommendedStrategy.recomp,
      'Auto-decided: novice + low BF — milk newbie gains via recomp.',
    );
  }
  if (bfPct < b.bulkStart) {
    return _StrategyDecision(
      RecommendedStrategy.bulk,
      'Auto-decided: BF below bulk start.',
    );
  }
  return _StrategyDecision(
    RecommendedStrategy.cut,
    'Auto-decided: default to cut.',
  );
}

extension on SexBoundaries {
  double hormonalFloor() => recompLimited; // recompLimited ≈ hormonal floor in our table
}

/// Public entry point. Returns strategy + rationale.
RecommendedStrategy decideStrategy(UserProfile profile, double bfPct) {
  return _decide(profile, bfPct).strategy;
}

/// Public entry point that also returns the rationale string.
(String, String) decideStrategyWithRationale(
    UserProfile profile, double bfPct) {
  final d = _decide(profile, bfPct);
  return (d.strategy.toJson(), d.rationale);
}
