/// Periodization: DUP day-type modifiers, Block phase modifiers, Strength phase
/// specs, Deload rules. See §9.12.
library;

import '../utils/round.dart';

/// DUP day-type modifiers (multipliers on reps_lo/hi, delta on RPE, multiplier on rest).
class DupModifiers {
  const DupModifiers(this.repsLoMult, this.repsHiMult, this.rpeDelta, this.restMult);
  final double repsLoMult;
  final double repsHiMult;
  final double rpeDelta;
  final double restMult;
}

const Map<String, Map<String, DupModifiers>> _dupTable = {
  'hypertrophy': {
    'heavy': DupModifiers(1.0, 1.0, 0.5, 1.5),
    'moderate': DupModifiers(1.2, 1.25, 0, 1.0),
    'light': DupModifiers(1.5, 1.6, -1.0, 0.6),
  },
  'strength': {
    'heavy': DupModifiers(0.5, 0.7, 0.5, 1.5),
    'moderate': DupModifiers(1.0, 1.0, 0, 1.0),
    'light': DupModifiers(1.5, 1.8, -1.0, 0.6),
  },
  'default': {
    'heavy': DupModifiers(0.8, 0.85, 0.5, 1.25),
    'moderate': DupModifiers(1.0, 1.0, 0, 1.0),
    'light': DupModifiers(1.25, 1.4, -1.0, 0.7),
  },
};

DupModifiers? dupModifiersFor(String? dayType, String family) {
  if (dayType == null) return null;
  final fam = _dupTable[family] ?? _dupTable['default']!;
  return fam[dayType];
}

/// Block phase modifiers (non-strength or non-compound-primary).
class BlockModifiers {
  const BlockModifiers(this.repsMult, this.setsDelta, this.rpeDelta);
  final double repsMult;
  final int setsDelta;
  final double rpeDelta;
}

const Map<String, BlockModifiers> _blockTable = {
  'accumulation': BlockModifiers(1.2, 1, -0.5),
  'intensification': BlockModifiers(0.6, -1, 1.0),
  'peak': BlockModifiers(0.5, -2, 1.5),
};

BlockModifiers? blockModifiersFor(String? phase) {
  if (phase == null) return null;
  return _blockTable[phase];
}

/// Strength phase specs (for STRENGTH goal + COMPOUND_PRIMARY).
class StrengthPhaseSpec {
  const StrengthPhaseSpec({
    required this.name,
    required this.durationWeeksMin,
    required this.durationWeeksMax,
    required this.mainSinglesPerWeek,
    required this.mainRpe,
    required this.secondarySetsPerWeek,
    required this.secondaryReps,
    required this.secondaryRir,
  });
  final String name;
  final int durationWeeksMin;
  final int durationWeeksMax;
  final String mainSinglesPerWeek; // "1-3"
  final String mainRpe; // "5-8"
  final String secondarySetsPerWeek; // "10-20"
  final String secondaryReps; // "6-20"
  final String secondaryRir; // "0-3"
}

const List<StrengthPhaseSpec> strengthPhases = [
  StrengthPhaseSpec(
    name: 'VOLUME',
    durationWeeksMin: 6,
    durationWeeksMax: 12,
    mainSinglesPerWeek: '1-3',
    mainRpe: '5-8',
    secondarySetsPerWeek: '10-20',
    secondaryReps: '6-20',
    secondaryRir: '0-3',
  ),
  StrengthPhaseSpec(
    name: 'LOAD',
    durationWeeksMin: 4,
    durationWeeksMax: 8,
    mainSinglesPerWeek: '2-4',
    mainRpe: '6-9',
    secondarySetsPerWeek: '5-10',
    secondaryReps: '6-20',
    secondaryRir: '0-3',
  ),
  StrengthPhaseSpec(
    name: 'PEAK',
    durationWeeksMin: 2,
    durationWeeksMax: 4,
    mainSinglesPerWeek: '2-5',
    mainRpe: '7-10',
    secondarySetsPerWeek: '0-4',
    secondaryReps: '6-20',
    secondaryRir: '0-3',
  ),
];

/// Deload modifiers: sets × 0.5, RPE − 1.5.
const double deloadSetsMultiplier = 0.5;
const double deloadRpeDelta = -1.5;

/// Apply DUP day-type modifier to a (reps_lo, reps_hi, rpe, rest) tuple.
({int repsLo, int repsHi, double rpe, int rest}) applyDup(
    DupModifiers m, int repsLo, int repsHi, double rpe, int rest) {
  // Rep-range math uses round-half-up.
  final newLo = (repsLo * m.repsLoMult).round();
  final newHi = (repsHi * m.repsHiMult).round();
  return (
    repsLo: newLo,
    repsHi: newHi,
    rpe: round1(rpe + m.rpeDelta),
    rest: (rest * m.restMult).round(),
  );
}

/// Apply Block phase modifier.
({int repsLo, int repsHi, int sets, double rpe}) applyBlock(
    BlockModifiers m, int repsLo, int repsHi, int sets, double rpe) {
  // Rep-range math uses round-half-up.
  return (
    repsLo: (repsLo * m.repsMult).round(),
    repsHi: (repsHi * m.repsMult).round(),
    sets: sets + m.setsDelta,
    rpe: round1(rpe + m.rpeDelta),
  );
}
