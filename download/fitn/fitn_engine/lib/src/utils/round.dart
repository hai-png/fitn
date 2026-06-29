/// Banker's rounding (round-half-to-even) and the round-half-up exception used
/// only for rep-range math. See spec §9.5.
///
/// Dart's `num.round()` is round-half-up by default; the engine must NOT use it
/// for anything except rep-range math. Everywhere else, use [roundBankers] /
/// [roundBankersToInt].
import 'dart:math' as math;

/// Round [value] to [decimals] decimal places using banker's rounding
/// (round-half-to-even).
///
/// Examples:
///   roundBankers(0.5, 0)  == 0
///   roundBankers(1.5, 0)  == 2
///   roundBankers(2.5, 0)  == 2
///   roundBankers(3.5, 0)  == 4
///   roundBankers(0.125, 2) == 0.12
///   roundBankers(0.135, 2) == 0.14
double roundBankers(double value, int decimals) {
  final factor = math.pow(10, decimals).toDouble();
  final scaled = value * factor;
  final floor = scaled.floorToDouble();
  final frac = scaled - floor;
  if (frac < 0.5) return floor / factor;
  if (frac > 0.5) return (floor + 1) / factor;
  // exact 0.5 → round to even
  final nearestEven = floor % 2 == 0 ? floor : floor + 1;
  return nearestEven / factor;
}

/// Round [value] to the nearest integer using banker's rounding.
int roundBankersToInt(double value) {
  final floor = value.floorToDouble();
  final frac = value - floor;
  if (frac < 0.5) return floor.toInt();
  if (frac > 0.5) return floor.toInt() + 1;
  return floor % 2 == 0 ? floor.toInt() : floor.toInt() + 1;
}

/// Round [value] to [decimals] using round-half-up (away from zero on tie).
///
/// Used ONLY for rep-range math so that "3-6" × 1.5 → "5-10" rather than the
/// banker's-rounded "4-11". See spec §11.14.
double roundHalfUp(double value, int decimals) {
  final factor = math.pow(10, decimals).toDouble();
  final scaled = value * factor;
  final floor = scaled.floorToDouble();
  final frac = scaled - floor;
  if (frac >= 0.5) {
    return (floor + 1) / factor;
  }
  return floor / factor;
}

/// Round [value] to 1 decimal place using banker's rounding.
double round1(double value) => roundBankers(value, 1);

/// Round [value] to 2 decimal places using banker's rounding.
double round2(double value) => roundBankers(value, 2);

/// Clamp [value] into the inclusive range [min, max].
double clampDouble(double value, double min, double max) {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

/// Clamp [value] into the inclusive range [min, max] (int variant).
int clampInt(int value, int min, int max) {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}
