/// Nutrition plan orchestrator. See spec §4.3 step 8.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/preferences.dart';
import '../models/nutrition.dart';
import '../models/assessment.dart';
import '../utils/round.dart';
import '../assessment/thresholds.dart';
import 'rmr.dart';
import 'tdee.dart';
import 'calories.dart';
import 'macros.dart';
import 'hydration.dart';
import 'micronutrients.dart';

/// Build the full nutrition plan.
NutritionPlan buildNutritionPlan({
  required UserProfile profile,
  required AssessmentResult assessment,
  required PlanPreferences prefs,
}) {
  final strategy = assessment.recommendedStrategy;

  // 1. RMR.
  final rmr = computeRMRWithAssessment(
    profile: profile,
    assessment: assessment,
    strategy: _strategyToCalorieStrategy(strategy),
    weightReducedPct: prefs.weightReducedPct,
  );

  // 2. TDEE.
  final tdee = computeTDEE(
    rmrKcal: rmr.adjustedRmrKcal,
    activityLevel: profile.activityLevel,
    weightLogKg: profile.weightLogKg,
    intakeLogKcal: profile.intakeLogKcal,
  );

  // 3. Calories.
  final calories = computeCalories(
    profile: profile,
    strategy: strategy,
    tdeeKcal: tdee.finalTdeeKcal,
  );

  // 4. Macros (use assessment's body fat % if user didn't provide one).
  final bodyFatPct = assessment.bodyComposition?.bodyFatPct ??
      profile.bodyFatPct ??
      20.0;
  final macros = computeMacros(
    profile: profile,
    strategy: calories.strategy,
    targetKcal: calories.targetCaloriesKcal,
    bodyFatPct: bodyFatPct,
  );

  // 5. Hydration.
  HydrationTarget hydration;
  try {
    hydration = computeHydration(
      profile: profile,
      exerciseHoursPerDay: prefs.exerciseHoursPerDay,
      exerciseIntensity: prefs.exerciseIntensity,
      climate: prefs.climate,
    );
  } catch (_) {
    // Pregnancy/breastfeeding set on male — fall back without those.
    hydration = computeHydration(
      profile: profile,
      exerciseHoursPerDay: prefs.exerciseHoursPerDay,
      exerciseIntensity: prefs.exerciseIntensity,
      climate: prefs.climate,
      isPregnant: false,
      isBreastfeeding: false,
    );
  }

  // 6. Micronutrients.
  final micros = computeMicronutrients(targetKcal: calories.targetCaloriesKcal);

  // 7. Timeline.
  final timeline = _computeTimelineWeeks(
    profile: profile,
    strategy: strategy,
    targetWeightKg: _targetWeightForTimeline(profile, assessment),
    bodyFatPct: bodyFatPct,
  );

  return NutritionPlan(
    rmr: rmr,
    tdee: tdee,
    calories: calories,
    macros: macros,
    hydration: hydration,
    micronutrients: micros,
    timelineWeeks: timeline,
    notes: [
      'Strategy: ${strategy.display}',
      'Target calories: ${round1(calories.targetCaloriesKcal)} kcal/day',
      'Timeline: $timeline weeks',
    ],
  );
}

CalorieStrategy _strategyToCalorieStrategy(RecommendedStrategy s) {
  return switch (s) {
    RecommendedStrategy.cut => CalorieStrategy.deficit,
    RecommendedStrategy.bulk => CalorieStrategy.surplus,
    RecommendedStrategy.maintenance => CalorieStrategy.maintenance,
    RecommendedStrategy.recomp => CalorieStrategy.recomp,
    RecommendedStrategy.habitChangeFirst => CalorieStrategy.maintenance,
    RecommendedStrategy.reverseDiet => CalorieStrategy.reverseDiet,
  };
}

/// Compute timeline (weeks). See §4.3 step 8.
int _computeTimelineWeeks({
  required UserProfile profile,
  required RecommendedStrategy strategy,
  required double targetWeightKg,
  required double bodyFatPct,
}) {
  final b = sexBoundaries(profile.sex);
  switch (strategy) {
    case RecommendedStrategy.cut:
      // max(4, floor(kgToLose / weeklyRateKg) + 4)
      // Target BF = operational_lo + 2.
      final targetBf = b.operationalLo + 2;
      final lbm = profile.weightKg * (1 - bodyFatPct / 100);
      final targetWeight = lbm / (1 - targetBf / 100);
      final kgToLose = (profile.weightKg - targetWeight).clamp(0.0, double.infinity);
      final rate = profile.cutRateTier?.ratePct ?? defaultCutRatePct_;
      final weeklyRateKg = profile.weightKg * rate;
      final weeks = (kgToLose / weeklyRateKg).floor() + 4;
      return weeks < 4 ? 4 : weeks;
    case RecommendedStrategy.bulk:
      // max(12, floor((targetGainKg / monthlyRateKg) × 4.348) + 4)
      // TargetGain = 5% BW.
      final targetGainKg = profile.weightKg * 0.05;
      // Default monthly rate by status (beginner 2%, novice 1.5%, intermediate 1%, advanced 0.5%).
      final monthlyRatePct = switch (profile.trainingStatus) {
        TrainingStatus.beginner => 0.02,
        TrainingStatus.novice => 0.015,
        TrainingStatus.intermediate => 0.01,
        TrainingStatus.advanced => 0.005,
      };
      final monthlyRateKg = profile.weightKg * monthlyRatePct;
      final weeks = ((targetGainKg / monthlyRateKg) * 4.348).floor() + 4;
      return weeks < 12 ? 12 : weeks;
    case RecommendedStrategy.recomp:
      return 12;
    case RecommendedStrategy.maintenance:
      return 12;
    case RecommendedStrategy.habitChangeFirst:
      return 8;
    case RecommendedStrategy.reverseDiet:
      return 8;
  }
}

const double defaultCutRatePct_ = 0.0075;

/// Compute a target weight (kg) used for timeline math.
double _targetWeightForTimeline(
    UserProfile profile, AssessmentResult assessment) {
  // Use the assessment's body composition targets if available.
  final bc = assessment.bodyComposition;
  if (bc != null) {
    return bc.targetWeightsKg['fitness'] ?? profile.weightKg;
  }
  return profile.weightKg;
}
