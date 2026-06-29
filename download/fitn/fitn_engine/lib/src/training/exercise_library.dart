/// Exercise library loader. See spec §4.4 step 5 + §9.4.
///
/// Loads + indexes `all_exercises.json`. The view-count parser and
/// secondary-muscle splitter live in [Exercise.fromJson].
library;

import 'dart:convert';
import 'dart:io';

import '../models/training.dart';
import '../models/enums.dart';

class ExerciseLibrary {
  ExerciseLibrary(this._exercises)
      : _bySlug = {for (final e in _exercises) e.slug: e},
        _byMuscle = _indexByMuscle(_exercises),
        _byEquipment = _indexByEquipment(_exercises),
        _byExperience = _indexByExperience(_exercises);

  final List<Exercise> _exercises;
  final Map<String, Exercise> _bySlug;
  final Map<String, List<Exercise>> _byMuscle;
  final Map<String, List<Exercise>> _byEquipment;
  final Map<ExperienceLevel, List<Exercise>> _byExperience;

  List<Exercise> get all => List.unmodifiable(_exercises);
  int get count => _exercises.length;

  Exercise? bySlug(String slug) => _bySlug[slug];

  List<Exercise> byMuscle(String muscle) =>
      _byMuscle[muscle.toLowerCase()] ?? const [];

  List<Exercise> byEquipment(String equipment) =>
      _byEquipment[equipment.toLowerCase()] ?? const [];

  List<Exercise> byExperience(ExperienceLevel lvl) =>
      _byExperience[lvl] ?? const [];

  /// Filter by equipment access — full_gym (33), home_gym (9), bodyweight_only (2).
  List<Exercise> filterByEquipmentAccess(EquipmentAccess access) {
    final allowed = _equipmentVocabulary(access);
    return _exercises
        .where((e) => allowed.contains(e.equipment.toLowerCase()))
        .toList();
  }

  /// Search by name (case-insensitive substring).
  List<Exercise> searchByName(String query) {
    if (query.isEmpty) return all;
    final q = query.toLowerCase();
    return _exercises
        .where((e) =>
            e.name.toLowerCase().contains(q) ||
            e.slug.toLowerCase().contains(q))
        .toList();
  }

  static Map<String, List<Exercise>> _indexByMuscle(List<Exercise> all) {
    final idx = <String, List<Exercise>>{};
    for (final e in all) {
      for (final m in e.muscleGroups) {
        idx.putIfAbsent(m.toLowerCase(), () => []).add(e);
      }
      for (final m in e.secondaryMuscles) {
        idx.putIfAbsent(m.toLowerCase(), () => []).add(e);
      }
    }
    return idx;
  }

  static Map<String, List<Exercise>> _indexByEquipment(List<Exercise> all) {
    final idx = <String, List<Exercise>>{};
    for (final e in all) {
      idx.putIfAbsent(e.equipment.toLowerCase(), () => []).add(e);
    }
    return idx;
  }

  static Map<ExperienceLevel, List<Exercise>> _indexByExperience(
      List<Exercise> all) {
    final idx = <ExperienceLevel, List<Exercise>>{};
    for (final e in all) {
      idx.putIfAbsent(e.experienceLevel, () => []).add(e);
    }
    return idx;
  }

  /// Equipment vocabulary per spec §9.4.
  static Set<String> _equipmentVocabulary(EquipmentAccess access) {
    return switch (access) {
      EquipmentAccess.fullGym => {
          'barbell', 'dumbbell', 'bodyweight', 'cable', 'machine', 'kettlebell',
          'bands', 'exercise ball', 'other', 'medicine ball', 'rope', 'sled',
          'foam roll', 'ez bar', 'landmine', 'box', 'lacrosse ball', 'trap bar',
          'jump rope', 'chains', 'tiger tail', 'bench', 'rings', 'valslide',
          'hipthruster', 'fat bar', 'safety bar', 'tire', 'weight plate',
          'plate', 'bar',
        },
      EquipmentAccess.homeGym => {
          'barbell', 'dumbbell', 'kettlebell', 'bodyweight', 'bands',
          'ez bar', 'landmine', 'trap bar', 'exercise ball',
        },
      EquipmentAccess.bodyweightOnly => {'bodyweight', 'bands'},
    };
  }
}

/// Load exercise library from `all_exercises.json`.
ExerciseLibrary loadExerciseLibrary(String jsonStr) {
  final decoded = jsonDecode(jsonStr) as Map<String, dynamic>;
  final exercisesMap = decoded['exercises'] as Map<String, dynamic>;
  final exercises = exercisesMap.values
      .map((e) => Exercise.fromJson(e as Map<String, dynamic>))
      .toList();
  return ExerciseLibrary(exercises);
}

/// Async load from a file path.
Future<ExerciseLibrary> loadExerciseLibraryFromFile(String path) async {
  final file = File(path);
  final contents = await file.readAsString();
  return loadExerciseLibrary(contents);
}
