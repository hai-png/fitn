/// Exercise categorization + movement-pattern detection.
/// See spec §4.4 step 5.
library;

import '../models/training.dart';
import '../models/enums.dart';
import '../exercise_library.dart';

/// Classify an exercise into a category (compound primary/secondary/accessory).
ExerciseCategory classifyExercise(Exercise e) {
  if (e.exerciseType.toLowerCase() == 'cardio') return ExerciseCategory.cardio;
  if (e.exerciseType.toLowerCase() == 'mobility' ||
      e.exerciseType.toLowerCase() == 'stretching') {
    return ExerciseCategory.mobility;
  }
  if (e.mechanics.toLowerCase() == 'compound') {
    // Compound primary = squat/bench/deadlift/ohp/row patterns.
    final slug = e.slug.toLowerCase();
    if (slug.contains('squat') ||
        slug.contains('bench') ||
        slug.contains('deadlift') ||
        slug.contains('press') ||
        slug.contains('row')) {
      return ExerciseCategory.compoundPrimary;
    }
    return ExerciseCategory.compoundSecondary;
  }
  return ExerciseCategory.accessory;
}

/// Detect movement pattern by keyword match. See §4.4 step 5.
///
/// Detection logic:
/// - Slug wins 100+length: if slug matches a pattern's keyword, that pattern wins
///   with weight 100 + slug length.
/// - Name wins length: if name matches a pattern's keyword, weight = keyword length.
/// - Force-type fallback: parse force_type root ("Push" → push family).
/// - Primary-muscle fallback: pattern whose primary_muscles contains the
///   exercise's first muscle group wins.
String? detectMovementPattern(Exercise e, Map<String, MovementPatternSpec> patterns) {
  String? best;
  double bestScore = 0;

  final slugLower = e.slug.toLowerCase();
  final nameLower = e.name.toLowerCase();

  for (final entry in patterns.entries) {
    final patternName = entry.key;
    final spec = entry.value;
    for (final keyword in spec.detectionKeywords) {
      final kw = keyword.toLowerCase();
      // Slug match wins 100 + length.
      if (slugLower.contains(kw)) {
        final score = 100 + kw.length;
        if (score > bestScore) {
          bestScore = score;
          best = patternName;
        }
        continue;
      }
      // Name match wins length.
      if (nameLower.contains(kw)) {
        final score = kw.length.toDouble();
        if (score > bestScore) {
          bestScore = score;
          best = patternName;
        }
      }
    }
  }

  if (best != null) return best;

  // Force-type fallback.
  final forceLower = e.forceType.toLowerCase();
  final forceRoot = forceRoot(forceLower);
  for (final entry in patterns.entries) {
    if (entry.value.family == forceRoot) {
      return entry.key;
    }
  }

  // Primary-muscle fallback.
  if (e.muscleGroups.isNotEmpty) {
    final primaryMuscle = e.muscleGroups.first;
    for (final entry in patterns.entries) {
      if (entry.value.primaryMuscles.contains(primaryMuscle)) {
        return entry.key;
      }
    }
  }

  return null;
}

/// Extract the force-type root: "Push (Bilateral)" → "push".
String forceRoot(String forceType) {
  if (forceType.contains('push')) return 'push';
  if (forceType.contains('pull')) return 'pull';
  if (forceType.contains('lower')) return 'lower';
  if (forceType.contains('arms')) return 'arms';
  if (forceType.contains('shoulders')) return 'shoulders';
  if (forceType.contains('core')) return 'core';
  if (forceType.contains('cardio')) return 'cardio';
  if (forceType.contains('mobility')) return 'mobility';
  return '';
}
