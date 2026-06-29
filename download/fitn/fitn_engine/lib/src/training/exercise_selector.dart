/// 7-tier exercise selector. See spec §4.4 step 5.
library;

import '../models/training.dart';
import '../models/enums.dart';
import 'exercise_library.dart';

/// Result of a selection attempt.
class SelectionResult {
  SelectionResult(this.exercise, this.tier);
  final Exercise exercise;
  final int tier; // 1-7
}

/// Select an exercise for a slot.
///
/// Filters:
/// - Equipment access (full_gym: 33 types, home_gym: 9, bodyweight_only: 2).
/// - Exclude CARDIO/MOBILITY categories; exclude plyometrics for beginners.
/// - 7 tiers progressively relax constraints.
Exercise? selectExerciseForSlot({
  required ExerciseLibrary library,
  required SlotSpec slot,
  required EquipmentAccess equipment,
  required TrainingStatus status,
  required Map<String, MovementPatternSpec> patterns,
}) {
  // Start with equipment-filtered set.
  final candidates = library.filterByEquipmentAccess(equipment);
  if (candidates.isEmpty) return null;

  // Exclude CARDIO/MOBILITY and plyometrics (for beginners).
  final filtered = candidates.where((e) {
    final typeLower = e.exerciseType.toLowerCase();
    if (typeLower == 'cardio') return false;
    if (typeLower == 'mobility' || typeLower == 'stretching') return false;
    if (status == TrainingStatus.beginner &&
        typeLower.contains('plyometric')) {
      return false;
    }
    return true;
  }).toList();

  if (filtered.isEmpty) return null;

  // === Tier 1: pattern + muscle + category + experience ===
  var tier1 = _tier(filtered, slot, patterns, status, strictExp: true);
  if (tier1 != null) return tier1;

  // === Tier 2: pattern + muscle + category (relax experience) ===
  var tier2 = _tier(filtered, slot, patterns, status, strictExp: false);
  if (tier2 != null) return tier2;

  // === Tier 3: pattern + muscle (relax category) ===
  final tier3 = _tierPatternAndMuscleOnly(filtered, slot, patterns);
  if (tier3 != null) return tier3;

  // === Tier 4: pattern only (relax muscle) ===
  final tier4 = _tierPatternOnly(filtered, slot, patterns);
  if (tier4 != null) return tier4;

  // === Tier 5: muscle only (relax pattern) ===
  final tier5 = _tierMuscleOnly(filtered, slot);
  if (tier5 != null) return tier5;

  // === Tier 6: category only ===
  final tier6 = _tierCategoryOnly(filtered, slot);
  if (tier6 != null) return tier6;

  // === Tier 7: any exercise (last resort) — pick highest-viewed ===
  filtered.sort((a, b) => b.views.compareTo(a.views));
  return filtered.isEmpty ? null : filtered.first;
}

Exercise? _tier(
  List<Exercise> pool,
  SlotSpec slot,
  Map<String, MovementPatternSpec> patterns,
  TrainingStatus status, {
  required bool strictExp,
}) {
  final patternSpec = patterns[slot.pattern];
  if (patternSpec == null) return null;

  final targetExp = _statusToExp(status);
  final matching = pool.where((e) {
    // Match primary muscle (case-insensitive).
    final hasMuscle =
        e.muscleGroups.any((m) => m.toLowerCase() == slot.primaryMuscle.toLowerCase());
    if (!hasMuscle) return false;
    if (strictExp && e.experienceLevel != targetExp) return false;
    return true;
  }).toList();

  if (matching.isEmpty) return null;
  return _pickBest(matching);
}

Exercise? _tierPatternAndMuscleOnly(
  List<Exercise> pool,
  SlotSpec slot,
  Map<String, MovementPatternSpec> patterns,
) {
  final matching = pool.where((e) {
    return e.muscleGroups
        .any((m) => m.toLowerCase() == slot.primaryMuscle.toLowerCase());
  }).toList();
  if (matching.isEmpty) return null;
  return _pickBest(matching);
}

Exercise? _tierPatternOnly(
  List<Exercise> pool,
  SlotSpec slot,
  Map<String, MovementPatternSpec> patterns,
) {
  // Look up exercises that have keywords from the pattern in their slug/name.
  final spec = patterns[slot.pattern];
  if (spec == null) return null;
  final matching = pool.where((e) {
    final slug = e.slug.toLowerCase();
    final name = e.name.toLowerCase();
    for (final kw in spec.detectionKeywords) {
      if (slug.contains(kw) || name.contains(kw)) return true;
    }
    return false;
  }).toList();
  if (matching.isEmpty) return null;
  return _pickBest(matching);
}

Exercise? _tierMuscleOnly(List<Exercise> pool, SlotSpec slot) {
  final matching = pool
      .where((e) => e.muscleGroups
          .any((m) => m.toLowerCase() == slot.primaryMuscle.toLowerCase()))
      .toList();
  if (matching.isEmpty) return null;
  return _pickBest(matching);
}

Exercise? _tierCategoryOnly(List<Exercise> pool, SlotSpec slot) {
  // Sort by view count and return the top one (no category match possible).
  if (pool.isEmpty) return null;
  return _pickBest(pool);
}

Exercise? _pickBest(List<Exercise> candidates) {
  if (candidates.isEmpty) return null;
  final sorted = List<Exercise>.from(candidates)
    ..sort((a, b) {
      // Sort by views desc, then by name asc.
      final viewCmp = b.views.compareTo(a.views);
      if (viewCmp != 0) return viewCmp;
      return a.name.compareTo(b.name);
    });
  return sorted.first;
}

ExperienceLevel _statusToExp(TrainingStatus s) {
  return switch (s) {
    TrainingStatus.beginner || TrainingStatus.novice =>
      ExperienceLevel.beginner,
    TrainingStatus.intermediate => ExperienceLevel.intermediate,
    TrainingStatus.advanced => ExperienceLevel.advanced,
  };
}
