/// Assessment orchestrator. See spec §4.2.
///
/// Runs 4 sub-assessments in order, never short-circuiting on failure:
///   1. assessBodyComposition
///   2. assessHealthRisk
///   3. assessMuscularPotential (skipped if bodyComp == null)
///   4. decideStrategy (skipped if bodyComp == null, defaults to maintenance)
///
/// If any sub-assessment throws, records `"sub_name: ArgumentError: <msg>"` in
/// errors and sets the sub-result to null. `is_partial = errors.isNotEmpty`.
library;

import '../models/enums.dart';
import '../models/profile.dart';
import '../models/assessment.dart';
import 'body_composition.dart';
import 'health_risk.dart';
import 'muscular_potential.dart';
import 'decision.dart';

/// Run the full assessment pipeline.
///
/// (Renamed from `assessProfile` to `runAssessment` to avoid clashing with the
/// `FitnEngine.assessProfile` method when both are imported.)
AssessmentResult runAssessment(UserProfile profile) {
  final errors = <String>[];
  BodyComposition? bodyComp;
  HealthRiskAssessment? healthRisk;
  MuscularPotential? muscularPotential;
  RecommendedStrategy strategy = RecommendedStrategy.maintenance;
  String rationale = '';

  // 1. Body composition.
  try {
    bodyComp = assessBodyComposition(profile);
  } catch (e) {
    errors.add('body_composition: $e');
  }

  // 2. Health risk (independent of body comp).
  try {
    healthRisk = assessHealthRisk(profile);
  } catch (e) {
    errors.add('health_risk: $e');
  }

  // 3. Muscular potential (skipped if bodyComp == null).
  if (bodyComp != null) {
    try {
      muscularPotential =
          assessMuscularPotential(profile, bodyComp.bodyFatPct);
    } catch (e) {
      errors.add('muscular_potential: $e');
    }
  }

  // 4. Strategy decision (skipped if bodyComp == null, defaults to maintenance).
  if (bodyComp != null) {
    try {
      final result = decideStrategyWithRationale(
          profile, bodyComp.bodyFatPct);
      strategy = RecommendedStrategyJson.fromJson(result.$1);
      rationale = result.$2;
    } catch (e) {
      errors.add('decision: $e');
    }
  } else {
    rationale = 'Body composition is unavailable — defaulting to maintenance.';
  }

  // Build summary defensively (every nullable field guarded).
  final summary = _buildSummary(profile, bodyComp, healthRisk,
      muscularPotential, strategy, rationale);

  return AssessmentResult(
    bodyComposition: bodyComp,
    healthRisk: healthRisk,
    muscularPotential: muscularPotential,
    recommendedStrategy: strategy,
    strategyRationale: rationale,
    summary: summary,
    isPartial: errors.isNotEmpty,
    errors: errors,
  );
}

String _buildSummary(
    UserProfile p,
    BodyComposition? bc,
    HealthRiskAssessment? hr,
    MuscularPotential? mp,
    RecommendedStrategy strategy,
    String rationale) {
  final parts = <String>[];
  parts.add(
      '${p.sex.display}, ${p.age}y, ${p.heightCm.toStringAsFixed(0)}cm, ${p.weightKg.toStringAsFixed(1)}kg');
  if (bc != null) {
    parts.add(
        'BF ${bc.bodyFatPct.toStringAsFixed(1)}% (${bc.bodyFatCategory.display}), BMI ${bc.bmi.toStringAsFixed(1)} (${bc.bmiCategory.display})');
  }
  if (hr != null) {
    parts.add('Overall risk: ${hr.overallRisk.display}');
  }
  if (mp != null) {
    parts.add(
        'FFMI ${mp.currentNormalizedFfmi.toStringAsFixed(1)} (${mp.ffmiToCeilingPct.toStringAsFixed(0)}% of natural ceiling)');
  }
  parts.add('Strategy: ${strategy.display}');
  if (rationale.isNotEmpty) parts.add(rationale);
  return parts.join(' · ');
}
