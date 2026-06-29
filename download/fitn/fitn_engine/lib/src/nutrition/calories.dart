/// Calorie targets. See spec §4.3 step 4.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/nutrition.dart';
import '../utils/round.dart';
import '../utils/units.dart';
import '../assessment/thresholds.dart';

/// Compute calorie targets by strategy.
///
/// Floors: 1200 (F) / 1500 (M).
CalorieTargets computeCalories({
  required UserProfile profile,
  required RecommendedStrategy strategy,
  required double tdeeKcal,
}) {
  final notes = <String>[];
  final floor = profile.sex == Sex.female ? 1200.0 : 1500.0;

  CalorieStrategy calorieStrategy;
  double ratePct;
  String rateLabel;
  double delta;

  switch (strategy) {
    case RecommendedStrategy.cut:
      calorieStrategy = CalorieStrategy.deficit;
      final cutRate = _resolveCutRate(profile);
      ratePct = cutRate;
      rateLabel = '${(cutRate * 100).toStringAsFixed(2)}% BW/week';
      // weeklyLoss (kg) = weightKg × rate
      // dailyDeficit = weeklyLoss × 1100
      final weeklyLoss = profile.weightKg * cutRate;
      delta = -(weeklyLoss * deficitKcalPerKgPerWeek);
      notes.add(
          'Cut: weekly loss ${round2(weeklyLoss)} kg → daily deficit ${round1(-delta)} kcal');
      break;
    case RecommendedStrategy.bulk:
      calorieStrategy = CalorieStrategy.surplus;
      final bulkRate = _resolveBulkRate(profile);
      ratePct = bulkRate;
      rateLabel = '${(bulkRate * 100).toStringAsFixed(2)}% BW/month';
      // monthlyGain (kg) = weightKg × rate
      // dailySurplus = monthlyGain × 330
      final monthlyGain = profile.weightKg * bulkRate;
      delta = monthlyGain * surplusKcalPerKgPerMonth;
      notes.add(
          'Bulk: monthly gain ${round2(monthlyGain)} kg → daily surplus ${round1(delta)} kcal');
      break;
    case RecommendedStrategy.maintenance:
      calorieStrategy = CalorieStrategy.maintenance;
      ratePct = 0;
      rateLabel = 'maintenance';
      delta = 0;
      notes.add('Maintenance: target = TDEE');
      break;
    case RecommendedStrategy.recomp:
      calorieStrategy = CalorieStrategy.recomp;
      // deficitPct by recomp potential — simplified to 0.10 (good).
      final deficitPct = _recompDeficitPct(profile);
      ratePct = deficitPct;
      rateLabel = 'recomp ${(deficitPct * 100).toStringAsFixed(0)}% deficit';
      delta = -tdeeKcal * deficitPct;
      notes.add(
          'Recomp: ${round1(deficitPct * 100)}% deficit → ${round1(-delta)} kcal');
      break;
    case RecommendedStrategy.habitChangeFirst:
      calorieStrategy = CalorieStrategy.maintenance;
      ratePct = 0;
      rateLabel = 'habit change (maintenance)';
      delta = 0;
      notes.add('Habit-change-first: same as maintenance');
      break;
    case RecommendedStrategy.reverseDiet:
      calorieStrategy = CalorieStrategy.reverseDiet;
      // Weekly ladder: +50/+100/+150 kcal/wk by aggressiveness, until target reached.
      // Simplified: assume +75 kcal/day average for the ladder.
      ratePct = 0;
      rateLabel = 'reverse-diet ladder (+50/+100/+150 kcal/wk)';
      delta = 75; // average daily increment
      notes.add(
          'Reverse-diet: weekly ladder +50/+100/+150 kcal (simplified to +75/day average)');
      break;
  }

  var target = tdeeKcal + delta;
  var floorApplied = false;
  if (target < floor) {
    target = floor;
    floorApplied = true;
    notes.add('Calorie floor applied: $floor kcal');
  }

  return CalorieTargets(
    strategy: calorieStrategy,
    baseTdeeKcal: round1(tdeeKcal),
    ratePct: ratePct,
    rateLabel: rateLabel,
    calorieDeltaKcal: round1(delta),
    targetCaloriesKcal: round1(target),
    calorieFloorApplied: floorApplied,
    floorKcal: floorApplied ? floor : null,
    notes: notes,
  );
}

/// Resolve cut rate: explicit tier → BF% threshold table → default 0.75%.
/// Hard cap 1.0% BW/week. See §4.3.
double _resolveCutRate(UserProfile p) {
  if (p.cutRateTier != null) {
    final tierRate = p.cutRateTier!.ratePct;
    return tierRate > maxWeeklyLossPct ? maxWeeklyLossPct : tierRate;
  }

  final bfPct = p.bodyFatPct;
  if (bfPct != null) {
    // Threshold table (first match). See §4.3.
    // Male thresholds [25, 20, 15] → rates [1.00, 0.75, 0.50, 0.50]
    // Female thresholds [32, 28, 22] → rates [1.00, 0.75, 0.50, 0.50]
    if (p.sex == Sex.male) {
      if (bfPct >= 25) return 0.010;
      if (bfPct >= 20) return 0.0075;
      if (bfPct >= 15) return 0.0050;
      return 0.0050;
    } else {
      if (bfPct >= 32) return 0.010;
      if (bfPct >= 28) return 0.0075;
      if (bfPct >= 22) return 0.0050;
      return 0.0050;
    }
  }
  return defaultCutRatePct;
}

/// Resolve bulk rate from aggressiveness × trainingStatus table. See §4.3.
double _resolveBulkRate(UserProfile p) {
  final aggro = p.bulkAggressiveness ?? BulkAggressiveness.happyMedium;
  final status = p.trainingStatus;

  // Table from §4.3.
  // Aggressiveness × Status → % BW/week
  // conservative: B/N 0.0020, I 0.0015, A 0.0010
  // happyMedium:  B/N 0.0050, I 0.00325, A 0.0015
  // aggressive:   B/N 0.0080, I 0.00575, A 0.0035
  // veryAggressive: B/N 0.0100, I 0.00800, A 0.0060
  switch (aggro) {
    case BulkAggressiveness.conservative:
      return switch (status) {
        TrainingStatus.beginner || TrainingStatus.novice => 0.0020,
        TrainingStatus.intermediate => 0.0015,
        TrainingStatus.advanced => 0.0010,
      };
    case BulkAggressiveness.happyMedium:
      return switch (status) {
        TrainingStatus.beginner || TrainingStatus.novice => 0.0050,
        TrainingStatus.intermediate => 0.00325,
        TrainingStatus.advanced => 0.0015,
      };
    case BulkAggressiveness.aggressive:
      return switch (status) {
        TrainingStatus.beginner || TrainingStatus.novice => 0.0080,
        TrainingStatus.intermediate => 0.00575,
        TrainingStatus.advanced => 0.0035,
      };
    case BulkAggressiveness.veryAggressive:
      return switch (status) {
        TrainingStatus.beginner || TrainingStatus.novice => 0.0100,
        TrainingStatus.intermediate => 0.00800,
        TrainingStatus.advanced => 0.0060,
      };
  }
}

/// Recomp deficit % by potential — 0.15 (excellent), 0.05 (good), 0.0 (limited).
double _recompDeficitPct(UserProfile p) {
  final bfPct = p.bodyFatPct;
  if (bfPct == null) return 0.10;
  final b = sexBoundaries(p.sex);
  if (bfPct >= b.recompExcellent) return 0.15;
  if (bfPct >= b.recompGoodLo) return 0.05;
  return 0.0;
}
