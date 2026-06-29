/// FFMI ceilings and named BF% target landmarks. See spec §4.2.4.
library;

import '../models/enums.dart';

/// FFMI natural common ceiling (Kouri 1995).
const double ffmiNaturalCommon = 25.0;

/// FFMI attainable ceiling.
const double ffmiAttainable = 27.3;

/// FFMI likely max ceiling.
const double ffmiLikelyMax = 28.0;

/// Normalization coefficient (6.1) and reference height (1.8 m).
const double ffmiNormalizationCoef = 6.1;
const double ffmiReferenceHeightM = 1.8;

/// Named target BF% landmarks by sex (spec §4.2.4 table).
///
/// Used to compute `targetWeightAtTargetBfKg` values.
class NamedBfTargets {
  const NamedBfTargets({
    required this.athletic,
    required this.fitness,
    required this.acceptable,
    required this.hormonalFloor,
  });

  final double athletic;
  final double fitness;
  final double acceptable;
  final double hormonalFloor;
}

const NamedBfTargets _maleTargets = NamedBfTargets(
  athletic: 14.0,
  fitness: 18.0,
  acceptable: 25.0,
  hormonalFloor: 10.0,
);

const NamedBfTargets _femaleTargets = NamedBfTargets(
  athletic: 21.0,
  fitness: 25.0,
  acceptable: 32.0,
  hormonalFloor: 18.0,
);

NamedBfTargets namedBfTargets(Sex sex) =>
    sex == Sex.male ? _maleTargets : _femaleTargets;

/// Expected monthly muscle gain (kg) — Lyle McDonald table.
///
/// Men gain at the listed rate; women gain at half (× 0.5).
const Map<TrainingStatus, double> monthlyMuscleGainKgMen = {
  TrainingStatus.beginner: 0.85,
  TrainingStatus.novice: 0.575,
  TrainingStatus.intermediate: 0.325,
  TrainingStatus.advanced: 0.10,
};
