/// Plan preferences model. See spec §4.1.2.
library;

import 'enums.dart';

class PlanPreferences {
  const PlanPreferences({
    this.exerciseHoursPerDay = 1.0,
    this.exerciseIntensity = ExerciseIntensity.moderate,
    this.climate = Climate.temperate,
    this.weightReducedPct = 0.0,
    this.muscleFocus,
    this.programDurationWeeks,
    this.mealFrequency = 3,
    this.cuisinePreference,
    this.allergensToAvoid,
    this.excludedIngredients,
    this.includePrePostWorkout = false,
  }) {
    if (exerciseHoursPerDay < 0.25 || exerciseHoursPerDay > 4) {
      throw ArgumentError(
          'exerciseHoursPerDay must be 0.25–4, got $exerciseHoursPerDay');
    }
    if (weightReducedPct < 0 || weightReducedPct > 1) {
      throw ArgumentError(
          'weightReducedPct must be 0.0–1.0, got $weightReducedPct');
    }
    if (mealFrequency < 2 || mealFrequency > 6) {
      throw ArgumentError('mealFrequency must be 2–6, got $mealFrequency');
    }
    if (programDurationWeeks != null &&
        (programDurationWeeks! < 4 || programDurationWeeks! > 52)) {
      throw ArgumentError(
          'programDurationWeeks must be 4–52 or null, got $programDurationWeeks');
    }
  }

  final double exerciseHoursPerDay;
  final ExerciseIntensity exerciseIntensity;
  final Climate climate;
  final double weightReducedPct;
  final List<String>? muscleFocus;
  final int? programDurationWeeks;
  final int mealFrequency;
  final String? cuisinePreference;
  final List<String>? allergensToAvoid;
  final List<String>? excludedIngredients;
  final bool includePrePostWorkout;

  factory PlanPreferences.fromJson(Map<String, dynamic> json) {
    return PlanPreferences(
      exerciseHoursPerDay:
          (json['exercise_hours_per_day'] as num? ?? 1.0).toDouble(),
      exerciseIntensity: json['exercise_intensity'] != null
          ? ExerciseIntensityJson.fromJson(json['exercise_intensity'] as String)
          : ExerciseIntensity.moderate,
      climate: json['climate'] != null
          ? ClimateJson.fromJson(json['climate'] as String)
          : Climate.temperate,
      weightReducedPct:
          (json['weight_reduced_pct'] as num? ?? 0.0).toDouble(),
      muscleFocus: (json['muscle_focus'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      programDurationWeeks: (json['program_duration_weeks'] as num?)?.toInt(),
      mealFrequency: (json['meal_frequency'] as num? ?? 3).toInt(),
      cuisinePreference: json['cuisine_preference'] as String?,
      allergensToAvoid: (json['allergens_to_avoid'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      excludedIngredients:
          (json['excluded_ingredients'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList(),
      includePrePostWorkout:
          (json['include_pre_post_workout'] as bool? ?? false),
    );
  }

  Map<String, dynamic> toJson() => {
        'exercise_hours_per_day': exerciseHoursPerDay,
        'exercise_intensity': exerciseIntensity.toJson(),
        'climate': climate.toJson(),
        'weight_reduced_pct': weightReducedPct,
        'muscle_focus': muscleFocus,
        'program_duration_weeks': programDurationWeeks,
        'meal_frequency': mealFrequency,
        'cuisine_preference': cuisinePreference,
        'allergens_to_avoid': allergensToAvoid,
        'excluded_ingredients': excludedIngredients,
        'include_pre_post_workout': includePrePostWorkout,
      };

  PlanPreferences copyWith({
    double? exerciseHoursPerDay,
    ExerciseIntensity? exerciseIntensity,
    Climate? climate,
    double? weightReducedPct,
    List<String>? muscleFocus,
    Object? programDurationWeeks = _sentinel,
    int? mealFrequency,
    Object? cuisinePreference = _sentinel,
    List<String>? allergensToAvoid,
    List<String>? excludedIngredients,
    bool? includePrePostWorkout,
  }) {
    return PlanPreferences(
      exerciseHoursPerDay: exerciseHoursPerDay ?? this.exerciseHoursPerDay,
      exerciseIntensity: exerciseIntensity ?? this.exerciseIntensity,
      climate: climate ?? this.climate,
      weightReducedPct: weightReducedPct ?? this.weightReducedPct,
      muscleFocus: muscleFocus ?? this.muscleFocus,
      programDurationWeeks: identical(programDurationWeeks, _sentinel)
          ? this.programDurationWeeks
          : programDurationWeeks as int?,
      mealFrequency: mealFrequency ?? this.mealFrequency,
      cuisinePreference: identical(cuisinePreference, _sentinel)
          ? this.cuisinePreference
          : cuisinePreference as String?,
      allergensToAvoid: allergensToAvoid ?? this.allergensToAvoid,
      excludedIngredients:
          excludedIngredients ?? this.excludedIngredients,
      includePrePostWorkout:
          includePrePostWorkout ?? this.includePrePostWorkout,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is PlanPreferences &&
          runtimeType == other.runtimeType &&
          exerciseHoursPerDay == other.exerciseHoursPerDay &&
          exerciseIntensity == other.exerciseIntensity &&
          climate == other.climate &&
          weightReducedPct == other.weightReducedPct &&
          _listEq(muscleFocus, other.muscleFocus) &&
          programDurationWeeks == other.programDurationWeeks &&
          mealFrequency == other.mealFrequency &&
          cuisinePreference == other.cuisinePreference &&
          _listEq(allergensToAvoid, other.allergensToAvoid) &&
          _listEq(excludedIngredients, other.excludedIngredients) &&
          includePrePostWorkout == other.includePrePostWorkout;

  @override
  int get hashCode => Object.hash(
        exerciseHoursPerDay,
        exerciseIntensity,
        climate,
        weightReducedPct,
        Object.hashAll(muscleFocus ?? const []),
        programDurationWeeks,
        mealFrequency,
        cuisinePreference,
        Object.hashAll(allergensToAvoid ?? const []),
        Object.hashAll(excludedIngredients ?? const []),
        includePrePostWorkout,
      );

  static bool _listEq(List<String>? a, List<String>? b) {
    if (a == null && b == null) return true;
    if (a == null || b == null) return false;
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }
}

const Object _sentinel = Object();
