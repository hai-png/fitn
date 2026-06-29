/// Sex-specific strategy boundaries. See spec §4.2.7 table.
///
/// Single source of truth for all sex-dependent decision-tree boundaries.
library;

import '../models/enums.dart';

class SexBoundaries {
  const SexBoundaries({
    required this.cutFloor,
    required this.bulkCeiling,
    required this.bulkStart,
    required this.operationalLo,
    required this.operationalHi,
    required this.obeseThreshold,
    required this.recompExcellent,
    required this.recompGoodLo,
    required this.recompLimited,
    required this.skinnyFatLo,
    required this.skinnyFatHi,
  });

  /// Below this BF% cutting is unsafe (protects hormones).
  final double cutFloor;

  /// Above this BF% bulking is not recommended (cut first).
  final double bulkCeiling;

  /// Below this BF% starting a bulk is reasonable.
  final double bulkStart;

  /// Lower bound of the operational BF% window.
  final double operationalLo;

  /// Upper bound of the operational BF% window.
  final double operationalHi;

  /// Obesity threshold (safety override triggers).
  final double obeseThreshold;

  /// BF% at which recomp is "excellent" potential.
  final double recompExcellent;

  /// Lower bound for "good" recomp potential.
  final double recompGoodLo;

  /// BF% below which recomp potential is limited.
  final double recompLimited;

  /// Lower bound of the skinny-fat window.
  final double skinnyFatLo;

  /// Upper bound of the skinny-fat window.
  final double skinnyFatHi;
}

const SexBoundaries _male = SexBoundaries(
  cutFloor: 10,
  bulkCeiling: 20,
  bulkStart: 15,
  operationalLo: 10,
  operationalHi: 20,
  obeseThreshold: 25,
  recompExcellent: 23,
  recompGoodLo: 15,
  recompLimited: 15,
  skinnyFatLo: 12,
  skinnyFatHi: 23,
);

const SexBoundaries _female = SexBoundaries(
  cutFloor: 18,
  bulkCeiling: 28,
  bulkStart: 23,
  operationalLo: 18,
  operationalHi: 28,
  obeseThreshold: 32,
  recompExcellent: 30,
  recompGoodLo: 25,
  recompLimited: 25,
  skinnyFatLo: 20,
  skinnyFatHi: 31,
);

/// Get the sex-specific boundary set.
SexBoundaries sexBoundaries(Sex sex) => switch (sex) {
      Sex.male => _male,
      Sex.female => _female,
    };
