/// Split design loader + picker. See spec §4.4 step 2.
library;

import 'dart:convert';
import 'dart:io';

import '../models/training.dart';
import '../models/enums.dart';

/// Load all split designs from `split_designs.json`.
List<SplitDesign> loadSplitDesigns(String jsonStr) {
  final list = jsonDecode(jsonStr) as List<dynamic>;
  return list
      .map((e) => SplitDesign.fromJson(e as Map<String, dynamic>))
      .toList();
}

Future<List<SplitDesign>> loadSplitDesignsFromFile(String path) async {
  final file = File(path);
  final contents = await file.readAsString();
  return loadSplitDesigns(contents);
}

/// Pick the best split design for the given parameters.
///
/// Filter chain (per §4.4 step 2):
/// 1. Filter by `days_per_week`.
/// 2. Filter by `experience` AND `goal`.
/// 3. Filter by `experience`.
/// 4. Filter by `goal`.
/// 5. All.
///
/// Tie-break by experience preference order.
SplitDesign pickSplit({
  required List<SplitDesign> splits,
  required int daysPerWeek,
  required TrainingStatus status,
  required TrainingGoal goal,
}) {
  final statusEnum = _statusToTrainingStatus(status);
  final goalEnum = goal;

  // 1. Filter by days_per_week.
  var candidates =
      splits.where((s) => s.daysPerWeek == daysPerWeek).toList();
  if (candidates.isEmpty) candidates = splits;

  // 2. By experience AND goal.
  var filtered = candidates
      .where((s) =>
          s.suitableForExperience.contains(statusEnum) &&
          s.suitableForGoals.contains(goalEnum))
      .toList();
  if (filtered.isNotEmpty) {
    filtered.sort((a, b) => _experiencePreference(status)
        .indexOf(a.splitType)
        .compareTo(_experiencePreference(status).indexOf(b.splitType)));
    return filtered.first;
  }

  // 3. By experience.
  filtered = candidates
      .where((s) => s.suitableForExperience.contains(statusEnum))
      .toList();
  if (filtered.isNotEmpty) {
    filtered.sort((a, b) => _experiencePreference(status)
        .indexOf(a.splitType)
        .compareTo(_experiencePreference(status).indexOf(b.splitType)));
    return filtered.first;
  }

  // 4. By goal.
  filtered = candidates
      .where((s) => s.suitableForGoals.contains(goalEnum))
      .toList();
  if (filtered.isNotEmpty) {
    filtered.sort((a, b) => _experiencePreference(status)
        .indexOf(a.splitType)
        .compareTo(_experiencePreference(status).indexOf(b.splitType)));
    return filtered.first;
  }

  // 5. All — pick by preference.
  candidates.sort((a, b) => _experiencePreference(status)
      .indexOf(a.splitType)
      .compareTo(_experiencePreference(status).indexOf(b.splitType)));
  return candidates.first;
}

/// Experience preference order (lower index = higher preference).
List<SplitType> _experiencePreference(TrainingStatus s) {
  return switch (s) {
    TrainingStatus.beginner => [
        SplitType.fullBody,
        SplitType.upperLower,
        SplitType.ppl,
      ],
    TrainingStatus.novice => [
        SplitType.fullBody,
        SplitType.upperLower,
        SplitType.ppl,
        SplitType.pushPull,
      ],
    TrainingStatus.intermediate => [
        SplitType.upperLower,
        SplitType.fullBody,
        SplitType.ppl,
        SplitType.pushPullLegsUpperLower,
        SplitType.pplX2,
      ],
    TrainingStatus.advanced => [
        SplitType.pplX2,
        SplitType.pushPullLegsUpperLower,
        SplitType.bodyPart,
        SplitType.upperLower,
        SplitType.fullBody,
      ],
  };
}

TrainingStatus _statusToTrainingStatus(TrainingStatus s) => s;
