/// Program presets for the training tab's preset selector.
///
/// NOTE: The exercise database is NOT hardcoded here — it comes from the
/// engine's 1,217-exercise database via [engineExercisesProvider].
/// See `lib/engine/engine_provider.dart`.
library;

/// Program preset — a pre-built multi-week training program.
class ProgramPreset {
  const ProgramPreset({
    required this.name,
    required this.description,
    required this.durationWeeks,
    required this.goal,
    required this.splitType,
    required this.daysPerWeek,
  });
  final String name;
  final String description;
  final int durationWeeks;
  final String goal;
  final String splitType;
  final int daysPerWeek;
}

class ProgramPresets {
  ProgramPresets._();

  static const List<ProgramPreset> all = [
    ProgramPreset(
      name: 'Hypertrophy Builder',
      description:
          '4-day upper/lower split focused on muscle accumulation. Moderate volume, progressive overload weekly.',
      durationWeeks: 8,
      goal: 'muscle-gain',
      splitType: 'Upper / Lower',
      daysPerWeek: 4,
    ),
    ProgramPreset(
      name: 'Powerlifting Peak',
      description:
          '3-day full-body strength block. Low reps, heavy compound lifts, linear progression.',
      durationWeeks: 12,
      goal: 'strength',
      splitType: 'Full Body',
      daysPerWeek: 3,
    ),
    ProgramPreset(
      name: 'Fat Shred Circuit',
      description:
          '5-day PPL + cardio hybrid. High volume, short rest, metabolic conditioning focus.',
      durationWeeks: 6,
      goal: 'weight-loss',
      splitType: 'Push / Pull / Legs',
      daysPerWeek: 5,
    ),
    ProgramPreset(
      name: 'Wellness Foundation',
      description:
          '2-day full-body maintenance plan. Light volume, balanced movements, sustainable frequency.',
      durationWeeks: 4,
      goal: 'general',
      splitType: 'Full Body',
      daysPerWeek: 2,
    ),
    ProgramPreset(
      name: 'Endurance Engine',
      description:
          '4-day hybrid strength + cardio block. Compound lifts + zone 2 work for VO2 max.',
      durationWeeks: 10,
      goal: 'endurance',
      splitType: 'Upper / Lower',
      daysPerWeek: 4,
    ),
  ];
}
