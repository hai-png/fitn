/// Plateau-detection and macro-tuning adjustment protocols.
/// See spec §2.2 (deferred wiring — engine has the logic).
///
/// These are kept simple; the UI wires them when the user has 3+ weeks of
/// weight logs.
library;

import '../models/enums.dart';
import '../models/profile.dart';

class CutAdjustmentRecommendation {
  CutAdjustmentRecommendation({
    required this.action,
    required this.reason,
    required this.newRatePct,
  });
  final String action;
  final String reason;
  final double newRatePct;
}

class BulkAdjustmentRecommendation {
  BulkAdjustmentRecommendation({
    required this.action,
    required this.reason,
    required this.newRatePct,
  });
  final String action;
  final String reason;
  final double newRatePct;
}

/// Detect plateau + suggest cut-rate adjustment.
CutAdjustmentRecommendation recommendCutAdjustment(UserProfile profile) {
  if (profile.weightLogKg.length < 21) {
    return CutAdjustmentRecommendation(
      action: 'continue',
      reason: 'Insufficient log data (<3 weeks).',
      newRatePct: 0.0075,
    );
  }
  // Look at last 3 weeks vs prior 3 weeks.
  final n = profile.weightLogKg.length;
  final recent = profile.weightLogKg.sublist(n - 7);
  final prior = profile.weightLogKg.sublist(n - 14, n - 7);
  final recentAvg = recent.reduce((a, b) => a + b) / recent.length;
  final priorAvg = prior.reduce((a, b) => a + b) / prior.length;
  final delta = priorAvg - recentAvg; // expected positive (weight loss)

  if (delta < 0.2) {
    // Plateau: scale cut rate up.
    return CutAdjustmentRecommendation(
      action: 'increase_rate',
      reason:
          'Weight loss has plateaued (Δ ${delta.toStringAsFixed(2)} kg over 3 weeks).',
      newRatePct: 0.010,
    );
  }
  if (delta > 1.5) {
    // Losing too fast — slow down.
    return CutAdjustmentRecommendation(
      action: 'decrease_rate',
      reason:
          'Weight loss too fast (Δ ${delta.toStringAsFixed(2)} kg over 3 weeks).',
      newRatePct: 0.005,
    );
  }
  return CutAdjustmentRecommendation(
    action: 'continue',
    reason: 'Weight loss on track (Δ ${delta.toStringAsFixed(2)} kg).',
    newRatePct: 0.0075,
  );
}

/// Detect plateau + suggest bulk-rate adjustment.
BulkAdjustmentRecommendation recommendBulkAdjustment(UserProfile profile) {
  if (profile.weightLogKg.length < 21) {
    return BulkAdjustmentRecommendation(
      action: 'continue',
      reason: 'Insufficient log data (<3 weeks).',
      newRatePct: 0.0050,
    );
  }
  final n = profile.weightLogKg.length;
  final recent = profile.weightLogKg.sublist(n - 7);
  final prior = profile.weightLogKg.sublist(n - 14, n - 7);
  final recentAvg = recent.reduce((a, b) => a + b) / recent.length;
  final priorAvg = prior.reduce((a, b) => a + b) / prior.length;
  final delta = recentAvg - priorAvg; // expected positive (weight gain)

  if (delta < 0.1) {
    return BulkAdjustmentRecommendation(
      action: 'increase_rate',
      reason:
          'Weight gain has plateaued (Δ ${delta.toStringAsFixed(2)} kg over 3 weeks).',
      newRatePct: 0.0080,
    );
  }
  if (delta > 0.7) {
    return BulkAdjustmentRecommendation(
      action: 'decrease_rate',
      reason:
          'Weight gain too fast (Δ ${delta.toStringAsFixed(2)} kg over 3 weeks) — risk of excess fat gain.',
      newRatePct: 0.00325,
    );
  }
  return BulkAdjustmentRecommendation(
    action: 'continue',
    reason: 'Weight gain on track (Δ ${delta.toStringAsFixed(2)} kg).',
    newRatePct: 0.0050,
  );
}
