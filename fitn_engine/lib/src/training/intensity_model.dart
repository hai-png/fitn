/// RIR/RPE intensity model. See spec §4.4 (RIR intensity tiers).
library;

/// RIR tier — maps to a (low, high) RIR range per rep range.
enum RirTier {
  lowerFreeWeightCompound,
  machineOrUpperPress,
  machinePressOrPull,
  isolation,
}

/// RIR ranges per tier × rep range. See §4.4.
const Map<RirTier, Map<String, List<int>>> _rirTable = {
  RirTier.lowerFreeWeightCompound: {
    '1-3': [0, 1],
    '4-6': [1, 3],
    '7-10': [2, 4],
    '11-20': [3, 5],
  },
  RirTier.machineOrUpperPress: {
    '1-3': [0, 2],
    '4-6': [1, 3],
    '7-10': [2, 4],
    '11-20': [3, 5],
  },
  RirTier.machinePressOrPull: {
    '1-3': [1, 3],
    '4-6': [2, 4],
    '7-10': [2, 4],
    '11-20': [3, 5],
  },
  RirTier.isolation: {
    '1-3': [1, 3],
    '4-6': [2, 4],
    '7-10': [2, 4],
    '11-20': [3, 5],
    '21-50': [4, 6],
  },
};

/// Lookup RIR range for a tier × rep-count.
List<int>? rirRange(RirTier tier, int reps) {
  final bucket = _repsToBucket(reps);
  if (bucket == null) return null;
  return _rirTable[tier]?[bucket];
}

String? _repsToBucket(int reps) {
  if (reps >= 1 && reps <= 3) return '1-3';
  if (reps >= 4 && reps <= 6) return '4-6';
  if (reps >= 7 && reps <= 10) return '7-10';
  if (reps >= 11 && reps <= 20) return '11-20';
  if (reps >= 21 && reps <= 50) return '21-50';
  return null;
}

/// Convert RIR to RPE: `RPE = clamp(10 − RIR, 4, 10)`.
double rpeFromRir(int rir) {
  final rpe = 10 - rir;
  if (rpe < 4) return 4;
  if (rpe > 10) return 10;
  return rpe.toDouble();
}
