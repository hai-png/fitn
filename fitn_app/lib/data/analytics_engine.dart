/// Analytics engine — ported from fitness-app's analyticsEngine.ts.
///
/// Computes:
/// - Epley 1RM estimation
/// - Core metrics (total volume, working sets, volume per minute)
/// - Rolling trends (7/30/365 day comparisons)
/// - Exercise progression analysis
/// - Personal records (max 1RM per exercise)
/// - Muscle volume zones + balance scores
/// - Lifetime volume tiers
library;

import '../data/domain_types.dart';

/// Epley formula: 1RM = weight × (1 + reps/30).
double calculateEpley1Rm(double weight, int reps) {
  if (reps <= 0 || weight <= 0) return 0;
  return weight * (1 + reps / 30);
}

/// Core metrics from a list of exercise logs.
class CoreMetrics {
  CoreMetrics({
    required this.totalVolume,
    required this.totalWorkingSets,
    required this.totalDuration,
    required this.volumePerMinute,
  });
  final double totalVolume;
  final int totalWorkingSets;
  final int totalDuration;
  final double volumePerMinute;
}

CoreMetrics calculateCoreMetrics(List<ExerciseLog> logs,
    {double secondaryMultiplier = 0.5}) {
  double totalVolume = 0;
  int workingSets = 0;
  int totalDuration = 0;
  for (final ex in logs) {
    totalDuration += ex.durationMinutes;
    for (final s in ex.sets) {
      if (s.isWarmUp) continue;
      workingSets++;
      totalVolume += s.weight * s.reps;
    }
  }
  final vpm = totalDuration > 0 ? totalVolume / totalDuration : 0.0;
  return CoreMetrics(
    totalVolume: totalVolume,
    totalWorkingSets: workingSets,
    totalDuration: totalDuration,
    volumePerMinute: vpm,
  );
}

/// Rolling trend comparison.
class RollingTrends {
  RollingTrends({
    required this.vol7,
    required this.vol30,
    required this.vol365,
    required this.diff7,
    required this.diff30,
    required this.diff365,
  });
  final double vol7;
  final double vol30;
  final double vol365;
  final double diff7;
  final double diff30;
  final double diff365;
}

RollingTrends calculateRollingTrends(List<ExerciseLog> logs) {
  final now = DateTime.now();
  double vol7 = 0, vol30 = 0, vol365 = 0;
  double prev7 = 0, prev30 = 0, prev365 = 0;
  for (final ex in logs) {
    final daysAgo = now.difference(ex.date).inDays;
    final vol = ex.sets.fold<double>(
        0, (s, set) => s + (set.isWarmUp ? 0 : set.weight * set.reps));
    if (daysAgo < 7) {
      vol7 += vol;
    } else if (daysAgo < 14) {
      prev7 += vol;
    }
    if (daysAgo < 30) {
      vol30 += vol;
    } else if (daysAgo < 60) {
      prev30 += vol;
    }
    if (daysAgo < 365) {
      vol365 += vol;
    } else if (daysAgo < 730) {
      prev365 += vol;
    }
  }
  double pct(double cur, double prev) =>
      prev > 0 ? ((cur - prev) / prev) * 100 : 0;
  return RollingTrends(
    vol7: vol7,
    vol30: vol30,
    vol365: vol365,
    diff7: pct(vol7, prev7),
    diff30: pct(vol30, prev30),
    diff365: pct(vol365, prev365),
  );
}

/// Exercise progression analysis — tracks 1RM over time for each exercise.
class ExerciseAnalysis {
  ExerciseAnalysis({
    required this.exerciseName,
    required this.targetMuscle,
    required this.sessions,
    required this.current1Rm,
    required this.best1Rm,
    required this.firstDate,
    required this.lastDate,
  });
  final String exerciseName;
  final String targetMuscle;
  final int sessions;
  final double current1Rm;
  final double best1Rm;
  final DateTime firstDate;
  final DateTime lastDate;
}

List<ExerciseAnalysis> analyzeExerciseProgression(List<ExerciseLog> logs) {
  final byExercise = <String, List<ExerciseLog>>{};
  for (final log in logs) {
    byExercise.putIfAbsent(log.exerciseName, () => []).add(log);
  }
  final results = <ExerciseAnalysis>[];
  for (final entry in byExercise.entries) {
    final name = entry.key;
    final sessions = entry.value..sort((a, b) => a.date.compareTo(b.date));
    double best1Rm = 0;
    double current1Rm = 0;
    for (final s in sessions) {
      for (final set in s.sets) {
        if (set.isWarmUp) continue;
        final e1rm = calculateEpley1Rm(set.weight, set.reps);
        if (e1rm > best1Rm) best1Rm = e1rm;
        current1Rm = e1rm;
      }
    }
    results.add(ExerciseAnalysis(
      exerciseName: name,
      targetMuscle: sessions.first.targetMuscle,
      sessions: sessions.length,
      current1Rm: current1Rm,
      best1Rm: best1Rm,
      firstDate: sessions.first.date,
      lastDate: sessions.last.date,
    ));
  }
  results.sort((a, b) => b.best1Rm.compareTo(a.best1Rm));
  return results;
}

/// Personal records — best 1RM per exercise.
List<PersonalRecord> calculatePersonalRecords(List<ExerciseLog> logs) {
  final analyses = analyzeExerciseProgression(logs);
  return analyses
      .map((a) => PersonalRecord(
            exerciseName: a.exerciseName,
            estimated1Rm: a.best1Rm,
            weight: a.best1Rm,
            reps: 1,
            date: a.lastDate,
          ))
      .toList();
}

/// Muscle volume zones — per-muscle total volume + balance percentage.
List<MuscleVolumeZone> calculateMuscleVolumesAndScores(
    List<ExerciseLog> logs, String trainingAge) {
  final byMuscle = <String, double>{};
  for (final ex in logs) {
    for (final s in ex.sets) {
      if (s.isWarmUp) continue;
      final vol = s.weight * s.reps;
      byMuscle[ex.targetMuscle] = (byMuscle[ex.targetMuscle] ?? 0) + vol;
    }
  }
  final totalVol = byMuscle.values.fold(0.0, (a, b) => a + b);
  final zones = <MuscleVolumeZone>[];
  for (final entry in byMuscle.entries) {
    final pct = totalVol > 0 ? (entry.value / totalVol) * 100 : 0.0;
    zones.add(MuscleVolumeZone(
      muscle: entry.key,
      totalVolumeKg: entry.value,
      balancePct: pct,
      zone: _zoneFor(entry.value, trainingAge),
    ));
  }
  zones.sort((a, b) => b.totalVolumeKg.compareTo(a.totalVolumeKg));
  return zones;
}

String _zoneFor(double volume, String trainingAge) {
  // Simplified zone classification based on volume.
  if (volume < 1000) return 'ML';
  if (volume < 5000) return 'MEV';
  if (volume < 20000) return 'MAV';
  return 'MRV';
}

/// Generate pre-seeded workout history for demo purposes.
List<ExerciseLog> generateWorkoutHistory() {
  final now = DateTime.now();
  return [
    ExerciseLog(
      id: 'seed-1',
      exerciseName: 'Flat Barbell Bench Press',
      targetMuscle: 'Chest',
      date: now.subtract(const Duration(days: 35)),
      sets: [
        ExerciseSetLog(id: 's1', weight: 60, reps: 8),
        ExerciseSetLog(id: 's2', weight: 65, reps: 6),
        ExerciseSetLog(id: 's3', weight: 70, reps: 5),
      ],
      durationMinutes: 12,
    ),
    ExerciseLog(
      id: 'seed-2',
      exerciseName: 'Flat Barbell Bench Press',
      targetMuscle: 'Chest',
      date: now.subtract(const Duration(days: 28)),
      sets: [
        ExerciseSetLog(id: 's4', weight: 65, reps: 8),
        ExerciseSetLog(id: 's5', weight: 70, reps: 6),
        ExerciseSetLog(id: 's6', weight: 72.5, reps: 5),
      ],
      durationMinutes: 12,
    ),
    ExerciseLog(
      id: 'seed-3',
      exerciseName: 'Flat Barbell Bench Press',
      targetMuscle: 'Chest',
      date: now.subtract(const Duration(days: 21)),
      sets: [
        ExerciseSetLog(id: 's7', weight: 70, reps: 8),
        ExerciseSetLog(id: 's8', weight: 72.5, reps: 6),
        ExerciseSetLog(id: 's9', weight: 75, reps: 5),
      ],
      durationMinutes: 12,
    ),
    ExerciseLog(
      id: 'seed-4',
      exerciseName: 'Barbell Back Squats',
      targetMuscle: 'Quads',
      date: now.subtract(const Duration(days: 30)),
      sets: [
        ExerciseSetLog(id: 's10', weight: 80, reps: 8),
        ExerciseSetLog(id: 's11', weight: 90, reps: 6),
        ExerciseSetLog(id: 's12', weight: 100, reps: 5),
      ],
      durationMinutes: 15,
    ),
    ExerciseLog(
      id: 'seed-5',
      exerciseName: 'Barbell Back Squats',
      targetMuscle: 'Quads',
      date: now.subtract(const Duration(days: 22)),
      sets: [
        ExerciseSetLog(id: 's13', weight: 90, reps: 8),
        ExerciseSetLog(id: 's14', weight: 100, reps: 6),
        ExerciseSetLog(id: 's15', weight: 105, reps: 5),
      ],
      durationMinutes: 15,
    ),
    ExerciseLog(
      id: 'seed-6',
      exerciseName: 'Lat Pulldown (Wide Grip)',
      targetMuscle: 'Lats',
      date: now.subtract(const Duration(days: 25)),
      sets: [
        ExerciseSetLog(id: 's16', weight: 50, reps: 12),
        ExerciseSetLog(id: 's17', weight: 55, reps: 10),
        ExerciseSetLog(id: 's18', weight: 60, reps: 8),
      ],
      durationMinutes: 10,
    ),
    ExerciseLog(
      id: 'seed-7',
      exerciseName: 'Romanian Deadlifts (RDL)',
      targetMuscle: 'Hamstrings',
      date: now.subtract(const Duration(days: 20)),
      sets: [
        ExerciseSetLog(id: 's19', weight: 70, reps: 10),
        ExerciseSetLog(id: 's20', weight: 80, reps: 8),
      ],
      durationMinutes: 10,
    ),
    ExerciseLog(
      id: 'seed-8',
      exerciseName: 'Dumbbell Shoulder Press',
      targetMuscle: 'Shoulders',
      date: now.subtract(const Duration(days: 18)),
      sets: [
        ExerciseSetLog(id: 's21', weight: 20, reps: 10),
        ExerciseSetLog(id: 's22', weight: 22.5, reps: 8),
      ],
      durationMinutes: 8,
    ),
  ];
}
