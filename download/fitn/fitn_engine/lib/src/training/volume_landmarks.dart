/// Volume landmarks + recommended weekly sets. See spec §4.4.
library;

import '../models/enums.dart';

class MuscleLandmarks {
  const MuscleLandmarks({
    required this.mev,
    required this.mavLo,
    required this.mavHi,
    required this.mrv,
    required this.ml,
  });

  /// Minimum Effective Volume (sets/muscle/week).
  final double mev;

  /// Maintenance Volume lower bound.
  final double mavLo;

  /// Maintenance Volume upper bound.
  final double mavHi;

  /// Maximum Recoverable Volume.
  final double mrv;

  /// Maintenance Level (when reducing volume).
  final double ml;

  double get mavMid => (mavLo + mavHi) / 2;
}

/// DEFAULT_MUSCLE_LANDMARKS — see §4.4 table.
const Map<String, MuscleLandmarks> defaultMuscleLandmarks = {
  'chest': MuscleLandmarks(mev: 8, mavLo: 10, mavHi: 22, mrv: 24, ml: 5),
  'back': MuscleLandmarks(mev: 10, mavLo: 14, mavHi: 22, mrv: 27, ml: 7),
  'upper_back': MuscleLandmarks(mev: 10, mavLo: 14, mavHi: 22, mrv: 27, ml: 7),
  'lats': MuscleLandmarks(mev: 10, mavLo: 14, mavHi: 22, mrv: 27, ml: 7),
  'middle_back': MuscleLandmarks(mev: 8, mavLo: 12, mavHi: 18, mrv: 22, ml: 5),
  'lower_back': MuscleLandmarks(mev: 3, mavLo: 4, mavHi: 8, mrv: 15, ml: 2),
  'traps': MuscleLandmarks(mev: 4, mavLo: 6, mavHi: 12, mrv: 18, ml: 3),
  'quads': MuscleLandmarks(mev: 8, mavLo: 12, mavHi: 20, mrv: 25, ml: 6),
  'hamstrings': MuscleLandmarks(mev: 6, mavLo: 10, mavHi: 16, mrv: 20, ml: 5),
  'glutes': MuscleLandmarks(mev: 4, mavLo: 8, mavHi: 16, mrv: 20, ml: 3),
  'adductors': MuscleLandmarks(mev: 4, mavLo: 6, mavHi: 12, mrv: 16, ml: 3),
  'abductors': MuscleLandmarks(mev: 4, mavLo: 6, mavHi: 12, mrv: 16, ml: 3),
  'hip_flexors': MuscleLandmarks(mev: 2, mavLo: 4, mavHi: 8, mrv: 10, ml: 2),
  'shoulders': MuscleLandmarks(mev: 6, mavLo: 8, mavHi: 16, mrv: 20, ml: 4),
  'side_delts': MuscleLandmarks(mev: 6, mavLo: 8, mavHi: 16, mrv: 20, ml: 4),
  'rear_delts': MuscleLandmarks(mev: 4, mavLo: 6, mavHi: 12, mrv: 16, ml: 3),
  'triceps': MuscleLandmarks(mev: 6, mavLo: 8, mavHi: 14, mrv: 18, ml: 4),
  'biceps': MuscleLandmarks(mev: 6, mavLo: 8, mavHi: 14, mrv: 20, ml: 4),
  'forearms': MuscleLandmarks(mev: 3, mavLo: 4, mavHi: 8, mrv: 15, ml: 2),
  'calves': MuscleLandmarks(mev: 8, mavLo: 10, mavHi: 16, mrv: 20, ml: 5),
  'abs': MuscleLandmarks(mev: 6, mavLo: 10, mavHi: 20, mrv: 25, ml: 5),
  'obliques': MuscleLandmarks(mev: 4, mavLo: 6, mavHi: 12, mrv: 18, ml: 3),
};

const MuscleLandmarks _fallback =
    MuscleLandmarks(mev: 6, mavLo: 10, mavHi: 16, mrv: 25, ml: 5);

/// Get landmarks for a muscle (falls back to the default).
MuscleLandmarks landmarksFor(String muscle) {
  final lower = muscle.toLowerCase();
  return defaultMuscleLandmarks[lower] ?? _fallback;
}

/// Recommended weekly sets = mavMid × tierMultiplier × goalMultiplier ×
/// experienceMultiplier, floored at ML (maintenance) or MEV (else).
double recommendedWeeklySets({
  required String muscle,
  required TrainingGoal goal,
  required TrainingStatus status,
  required VolumeTier tier,
}) {
  final l = landmarksFor(muscle);
  final goalMult = _goalMultiplier(goal);
  final expMult = _experienceMultiplier(status);
  final tierMult = tier.multiplier;
  final raw = l.mavMid * tierMult * goalMult * expMult;
  final floor = (goal == TrainingGoal.maintenance) ? l.ml : l.mev;
  return raw < floor ? floor : raw;
}

double _goalMultiplier(TrainingGoal g) {
  return switch (g) {
    TrainingGoal.hypertrophy || TrainingGoal.muscleGain => 1.0,
    TrainingGoal.recomp => 0.9,
    TrainingGoal.strength => 0.7,
    TrainingGoal.fatLoss => 0.8,
    TrainingGoal.maintenance => 0.6,
    TrainingGoal.generalFitness => 0.7,
  };
}

double _experienceMultiplier(TrainingStatus s) {
  return switch (s) {
    TrainingStatus.beginner => 0.7,
    TrainingStatus.novice => 0.85,
    TrainingStatus.intermediate => 1.0,
    TrainingStatus.advanced => 1.1,
  };
}

/// Volume tier (MINIMAL/LOW/MEDIUM/HIGH/VERY_HIGH → 4-8/9-12/13-16/17-20/21-30
/// sets/muscle/wk).
enum VolumeTier {
  minimal(0.5),
  low(0.7),
  medium(1.0),
  high(1.3),
  veryHigh(1.7);

  const VolumeTier(this.multiplier);
  final double multiplier;
}
