/// Engine provider + plan generation wrapper. See spec §6.4.
library;

import 'dart:isolate';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';

/// Loads the engine once at app startup.
final engineProvider = FutureProvider<FitnEngine>((ref) async {
  final data = await loadEngineData();
  return FitnEngine(data: data);
});

/// The singleton engine data (kept loaded for passing to isolates).
EngineData? _engineDataSingleton;

Future<EngineData> getEngineData() async {
  _engineDataSingleton ??= await loadEngineData();
  return _engineDataSingleton!;
}

/// Generate a plan in an isolate (off the UI thread). See §6.4.
///
/// The engine is 200-500ms on a mid-range phone; isolating keeps the UI smooth.
Future<FitnessPlan> generatePlanInIsolate({
  required UserProfile profile,
  required PlanPreferences prefs,
  required EngineData engineData,
}) async {
  return Isolate.run(() {
    final engine = FitnEngine(data: engineData);
    final assessment = engine.assessProfile(profile);
    if (assessment.isPartial) {
      throw PartialAssessmentError(assessment.errors);
    }
    return engine.proposePlan(profile, assessment, prefs);
  });
}

/// Convenience: generate plan + assessment in one call (isolated).
Future<GeneratePlanResponse> generatePlanResponseInIsolate({
  required UserProfile profile,
  required PlanPreferences prefs,
  required EngineData engineData,
}) async {
  return Isolate.run(() {
    final engine = FitnEngine(data: engineData);
    return engine.generatePlan(profile, prefs);
  });
}
