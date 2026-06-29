/// Training plan output models. See spec §9.1 (output tree).
library;

import 'enums.dart';

/// Movement pattern specification loaded from `movement_patterns.json`.
class MovementPatternSpec {
  MovementPatternSpec({
    required this.name,
    required this.family,
    required this.primaryMuscles,
    required this.detectionKeywords,
    required this.envPreference,
  });

  final String name;
  final String family;
  final List<String> primaryMuscles;
  final List<String> detectionKeywords;
  final Map<String, List<String>> envPreference;

  factory MovementPatternSpec.fromJson(String name, Map<String, dynamic> json) {
    return MovementPatternSpec(
      name: name,
      family: json['family'] as String,
      primaryMuscles: (json['primary_muscles'] as List).cast<String>(),
      detectionKeywords:
          (json['detection_keywords'] as List).cast<String>(),
      envPreference: (json['env_preference'] as Map).map((k, v) =>
          MapEntry(k as String, (v as List).cast<String>())),
    );
  }
}

/// Exercise entry (from `all_exercises.json`).
class Exercise {
  Exercise({
    required this.slug,
    required this.name,
    required this.equipment,
    required this.mechanics,
    required this.forceType,
    required this.experienceLevel,
    required this.exerciseType,
    required this.muscleGroups,
    required this.secondaryMuscles,
    required this.views,
    required this.overview,
    required this.instructions,
    required this.tips,
    this.videoUrl,
    this.videoId,
    this.videoThumbnail,
    this.url,
    this.targetMuscleGroup,
    this.categories,
  });

  final String slug;
  final String name;
  final String equipment;
  final String mechanics;
  final String forceType;
  final ExperienceLevel experienceLevel;
  final String exerciseType;
  final List<String> muscleGroups;
  final List<String> secondaryMuscles;
  final int views;
  final String overview;
  final List<String> instructions;
  final List<String> tips;
  final String? videoUrl;
  final String? videoId;
  final String? videoThumbnail;
  final String? url;
  final String? targetMuscleGroup;
  final List<String>? categories;

  factory Exercise.fromJson(Map<String, dynamic> json) {
    return Exercise(
      slug: json['slug'] as String,
      name: json['name'] as String,
      equipment: json['equipment'] as String,
      mechanics: json['mechanics'] as String,
      forceType: json['force_type'] as String,
      experienceLevel: _parseExperienceLevel(
          json['experience_level'] as String? ?? 'Intermediate'),
      exerciseType: json['exercise_type'] as String? ?? 'Strength',
      muscleGroups: ((json['categories'] as List?) ?? const [])
          .map((e) => (e as String).toLowerCase())
          .toList(),
      secondaryMuscles: _parseSecondaryMuscles(json['secondary_muscles']),
      views: _parseViews(json['views'] as String?),
      overview: json['overview'] as String? ?? '',
      instructions: ((json['instructions'] as List?) ?? const [])
          .map((e) => e as String)
          .toList(),
      tips: ((json['tips'] as List?) ?? const [])
          .map((e) => e as String)
          .toList(),
      videoUrl: json['video_url'] as String?,
      videoId: json['video_id'] as String?,
      videoThumbnail: json['video_thumbnail'] as String?,
      url: json['url'] as String?,
      targetMuscleGroup: json['target_muscle_group'] as String?,
      categories: (json['categories'] as List?)
          ?.map((e) => e as String)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'slug': slug,
        'name': name,
        'equipment': equipment,
        'mechanics': mechanics,
        'force_type': forceType,
        'experience_level': experienceLevel.name[0].toUpperCase() +
            experienceLevel.name.substring(1),
        'exercise_type': exerciseType,
        'categories': muscleGroups,
        'secondary_muscles': secondaryMuscles.join(', '),
        'views': _formatViews(views),
        'overview': overview,
        'instructions': instructions,
        'tips': tips,
        'video_url': videoUrl,
        'video_id': videoId,
        'video_thumbnail': videoThumbnail,
        'url': url,
        'target_muscle_group': targetMuscleGroup,
      };

  static ExperienceLevel _parseExperienceLevel(String s) {
    final lower = s.toLowerCase();
    if (lower.contains('beginner')) return ExperienceLevel.beginner;
    if (lower.contains('advanced')) return ExperienceLevel.advanced;
    return ExperienceLevel.intermediate;
  }

  static List<String> _parseSecondaryMuscles(dynamic v) {
    if (v == null) return const [];
    if (v is String) {
      return v
          .split(',')
          .map((s) => s.trim().toLowerCase())
          .where((s) => s.isNotEmpty)
          .toList();
    }
    if (v is List) {
      return v.map((e) => (e as String).toLowerCase()).toList();
    }
    return const [];
  }

  /// Parse view-count strings like "6.6M", "12K", "12345" into an integer.
  static int _parseViews(String? s) {
    if (s == null || s.isEmpty) return 0;
    final trimmed = s.trim();
    final lower = trimmed.toLowerCase();
    try {
      if (lower.endsWith('m')) {
        return (double.parse(lower.substring(0, lower.length - 1)) * 1e6)
            .round();
      }
      if (lower.endsWith('k')) {
        return (double.parse(lower.substring(0, lower.length - 1)) * 1e3)
            .round();
      }
      return int.parse(trimmed);
    } catch (_) {
      return 0;
    }
  }

  static String _formatViews(int v) {
    if (v >= 1e6) return '${(v / 1e6).toStringAsFixed(1)}M';
    if (v >= 1e3) return '${(v / 1e3).toStringAsFixed(1)}K';
    return v.toString();
  }
}

/// A slot in a workout template (filled by an exercise).
class SlotSpec {
  SlotSpec({
    required this.name,
    required this.primaryMuscle,
    required this.pattern,
    required this.category,
    required this.sets,
    this.secondaryMuscles = const [],
    this.forceTypeHint,
    this.isFocusEmphasis = false,
  });

  final String name;
  final String primaryMuscle;
  final String pattern;
  final ExerciseCategory category;
  final int sets;
  final List<String> secondaryMuscles;
  final String? forceTypeHint;
  final bool isFocusEmphasis;

  factory SlotSpec.fromJson(Map<String, dynamic> json) {
    return SlotSpec(
      name: json['name'] as String,
      primaryMuscle: json['primary_muscle'] as String,
      pattern: json['pattern'] as String,
      category: _exerciseCategoryFromString(json['category'] as String),
      sets: (json['sets'] as num).toInt(),
      secondaryMuscles:
          (json['secondary_muscles'] as List? ?? const []).cast<String>(),
      forceTypeHint: json['force_type_hint'] as String?,
      isFocusEmphasis: (json['is_focus_emphasis'] as bool? ?? false),
    );
  }
}

/// A workout template within a split design.
class WorkoutTemplate {
  WorkoutTemplate({
    required this.name,
    required this.focus,
    this.dayType,
    required this.slots,
  });

  final String name;
  final String focus;
  final String? dayType; // null | "heavy" | "moderate" | "light"
  final List<SlotSpec> slots;

  factory WorkoutTemplate.fromJson(Map<String, dynamic> json) {
    return WorkoutTemplate(
      name: json['name'] as String,
      focus: json['focus'] as String? ?? '',
      dayType: json['day_type'] as String?,
      slots: ((json['slots'] as List?) ?? const [])
          .map((e) => SlotSpec.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

/// A loaded split design (from `split_designs.json`).
class SplitDesign {
  SplitDesign({
    required this.name,
    required this.splitType,
    required this.daysPerWeek,
    required this.description,
    required this.templates,
    required this.restDays,
    required this.suitableForExperience,
    required this.suitableForGoals,
  });

  final String name;
  final SplitType splitType;
  final int daysPerWeek;
  final String description;
  final List<WorkoutTemplate> templates;
  final List<int> restDays;
  final List<TrainingStatus> suitableForExperience;
  final List<TrainingGoal> suitableForGoals;

  factory SplitDesign.fromJson(Map<String, dynamic> json) {
    return SplitDesign(
      name: json['name'] as String,
      splitType: _splitTypeFromString(json['split_type'] as String),
      daysPerWeek: (json['days_per_week'] as num).toInt(),
      description: json['description'] as String? ?? '',
      templates: ((json['templates'] as List?) ?? const [])
          .map((e) => WorkoutTemplate.fromJson(e as Map<String, dynamic>))
          .toList(),
      restDays: ((json['rest_days'] as List?) ?? const [])
          .map((e) => (e as num).toInt())
          .toList(),
      suitableForExperience: ((json['suitable_for_experience'] as List)
              .map((e) => _trainingStatusFromString(e as String)))
          .toList(),
      suitableForGoals: ((json['suitable_for_goals'] as List)
              .map((e) => _trainingGoalFromString(e as String)))
          .toList(),
    );
  }
}

class WorkoutExercise {
  WorkoutExercise({
    required this.exercise,
    required this.sets,
    required this.reps,
    required this.restSec,
    this.rpeTarget,
    required this.notes,
    required this.category,
  });

  final Exercise exercise;
  final int sets;
  final String reps;
  final int restSec;
  final double? rpeTarget;
  final List<String> notes;
  final ExerciseCategory category;

  Map<String, dynamic> toJson() => {
        'exercise': exercise.toJson(),
        'sets': sets,
        'reps': reps,
        'rest_sec': restSec,
        'rpe_target': rpeTarget,
        'notes': notes,
        'category': category.toJson(),
      };

  factory WorkoutExercise.fromJson(Map<String, dynamic> json) {
    return WorkoutExercise(
      exercise:
          Exercise.fromJson(json['exercise'] as Map<String, dynamic>),
      sets: (json['sets'] as num).toInt(),
      reps: json['reps'] as String,
      restSec: (json['rest_sec'] as num).toInt(),
      rpeTarget: (json['rpe_target'] as num?)?.toDouble(),
      notes: (json['notes'] as List).cast<String>(),
      category:
          _exerciseCategoryFromString(json['category'] as String),
    );
  }
}

class Workout {
  Workout({
    required this.dayNumber,
    required this.name,
    required this.focus,
    required this.exercises,
    required this.estimatedDurationMin,
    required this.notes,
  });

  final int dayNumber;
  final String name;
  final String focus;
  final List<WorkoutExercise> exercises;
  final int estimatedDurationMin;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'day_number': dayNumber,
        'name': name,
        'focus': focus,
        'exercises': exercises.map((e) => e.toJson()).toList(),
        'estimated_duration_min': estimatedDurationMin,
        'notes': notes,
      };

  factory Workout.fromJson(Map<String, dynamic> json) {
    return Workout(
      dayNumber: (json['day_number'] as num).toInt(),
      name: json['name'] as String,
      focus: json['focus'] as String? ?? '',
      exercises: ((json['exercises'] as List?) ?? const [])
          .map((e) => WorkoutExercise.fromJson(e as Map<String, dynamic>))
          .toList(),
      estimatedDurationMin: (json['estimated_duration_min'] as num).toInt(),
      notes: (json['notes'] as List? ?? const []).cast<String>(),
    );
  }
}

class Microcycle {
  Microcycle({
    required this.name,
    required this.workouts,
    required this.restDays,
    required this.isDeload,
  });

  final String name;
  final List<Workout> workouts;
  final List<int> restDays;
  final bool isDeload;

  Map<String, dynamic> toJson() => {
        'name': name,
        'workouts': workouts.map((e) => e.toJson()).toList(),
        'rest_days': restDays,
        'is_deload': isDeload,
      };

  factory Microcycle.fromJson(Map<String, dynamic> json) {
    return Microcycle(
      name: json['name'] as String,
      workouts: ((json['workouts'] as List?) ?? const [])
          .map((e) => Workout.fromJson(e as Map<String, dynamic>))
          .toList(),
      restDays: ((json['rest_days'] as List?) ?? const [])
          .map((e) => (e as num).toInt())
          .toList(),
      isDeload: (json['is_deload'] as bool? ?? false),
    );
  }
}

class Mesocycle {
  Mesocycle({
    required this.name,
    required this.durationWeeks,
    required this.progression,
    required this.microcycles,
    required this.deloadWeek,
    required this.notes,
  });

  final String name;
  final int durationWeeks;
  final ProgressionScheme progression;
  final List<Microcycle> microcycles;
  final bool deloadWeek;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'name': name,
        'duration_weeks': durationWeeks,
        'progression': progression.toJson(),
        'microcycles': microcycles.map((e) => e.toJson()).toList(),
        'deload_week': deloadWeek,
        'notes': notes,
      };

  factory Mesocycle.fromJson(Map<String, dynamic> json) {
    return Mesocycle(
      name: json['name'] as String,
      durationWeeks: (json['duration_weeks'] as num).toInt(),
      progression:
          ProgressionSchemeJson.fromJson(json['progression'] as String),
      microcycles: ((json['microcycles'] as List?) ?? const [])
          .map((e) => Microcycle.fromJson(e as Map<String, dynamic>))
          .toList(),
      deloadWeek: (json['deload_week'] as bool? ?? false),
      notes: (json['notes'] as List? ?? const []).cast<String>(),
    );
  }
}

class TrainingPlan {
  TrainingPlan({
    required this.goal,
    required this.splitType,
    required this.trainingDaysPerWeek,
    required this.progression,
    required this.mesocycles,
    required this.totalDurationWeeks,
    required this.muscleFocus,
    required this.weeklyVolumeSummary,
    required this.notes,
  });

  final TrainingGoal goal;
  final SplitType splitType;
  final int trainingDaysPerWeek;
  final ProgressionScheme progression;
  final List<Mesocycle> mesocycles;
  final int totalDurationWeeks;
  final List<String> muscleFocus;
  final Map<String, double> weeklyVolumeSummary;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'goal': goal.toJson(),
        'split_type': splitType.toJson(),
        'training_days_per_week': trainingDaysPerWeek,
        'progression': progression.toJson(),
        'mesocycles': mesocycles.map((e) => e.toJson()).toList(),
        'total_duration_weeks': totalDurationWeeks,
        'muscle_focus': muscleFocus,
        'weekly_volume_summary': weeklyVolumeSummary,
        'notes': notes,
      };

  factory TrainingPlan.fromJson(Map<String, dynamic> json) {
    return TrainingPlan(
      goal: TrainingGoalJson.fromJson(json['goal'] as String),
      splitType: SplitTypeJson.fromJson(json['split_type'] as String),
      trainingDaysPerWeek: (json['training_days_per_week'] as num).toInt(),
      progression:
          ProgressionSchemeJson.fromJson(json['progression'] as String),
      mesocycles: ((json['mesocycles'] as List?) ?? const [])
          .map((e) => Mesocycle.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalDurationWeeks: (json['total_duration_weeks'] as num).toInt(),
      muscleFocus: ((json['muscle_focus'] as List?) ?? const [])
          .cast<String>(),
      weeklyVolumeSummary:
          (json['weekly_volume_summary'] as Map).map(
              (k, v) => MapEntry(k as String, (v as num).toDouble())),
      notes: (json['notes'] as List? ?? const []).cast<String>(),
    );
  }
}

// === String → enum converters ===

ExerciseCategory _exerciseCategoryFromString(String s) {
  // snake_case → camelCase → enum
  final lower = s.toLowerCase();
  final mapped = {
    'compound_primary': ExerciseCategory.compoundPrimary,
    'compound_secondary': ExerciseCategory.compoundSecondary,
    'accessory': ExerciseCategory.accessory,
    'cardio': ExerciseCategory.cardio,
    'mobility': ExerciseCategory.mobility,
  };
  return mapped[lower] ?? ExerciseCategory.accessory;
}

SplitType _splitTypeFromString(String s) {
  final lower = s.toLowerCase();
  final mapped = {
    'full_body': SplitType.fullBody,
    'upper_lower': SplitType.upperLower,
    'ppl': SplitType.ppl,
    'pplX2'.toLowerCase(): SplitType.pplX2,
    'ppl_x2': SplitType.pplX2,
    'push_pull_legs_upper_lower': SplitType.pushPullLegsUpperLower,
    'pushpulllegsupperlower': SplitType.pushPullLegsUpperLower,
    'body_part': SplitType.bodyPart,
    'bodypart': SplitType.bodyPart,
    'push_pull': SplitType.pushPull,
    'pushpull': SplitType.pushPull,
  };
  return mapped[lower] ?? SplitType.fullBody;
}

TrainingStatus _trainingStatusFromString(String s) {
  final lower = s.toLowerCase();
  return switch (lower) {
    'beginner' => TrainingStatus.beginner,
    'novice' => TrainingStatus.novice,
    'intermediate' => TrainingStatus.intermediate,
    'advanced' => TrainingStatus.advanced,
    _ => TrainingStatus.beginner,
  };
}

TrainingGoal _trainingGoalFromString(String s) {
  final lower = s.toLowerCase();
  return switch (lower) {
    'strength' => TrainingGoal.strength,
    'hypertrophy' => TrainingGoal.hypertrophy,
    'general_fitness' => TrainingGoal.generalFitness,
    'fat_loss' => TrainingGoal.fatLoss,
    'muscle_gain' => TrainingGoal.muscleGain,
    'recomp' => TrainingGoal.recomp,
    'maintenance' => TrainingGoal.maintenance,
    _ => TrainingGoal.hypertrophy,
  };
}
