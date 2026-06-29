/// Unit conversion constants and helpers. See spec §9.7.
import 'dart:math' as math;

// === Conversion constants (§9.7) ===

/// Weeks per month — precise value, NOT 4.345.
const double weeksPerMonth = 4.348;

/// Energy density of body fat (kcal/kg).
const double kcalPerKgFat = 7700;

/// Energy density of body fat (kcal/lb).
const double kcalPerLbFat = 3500;

/// Energy cost of building 1 lb of muscle (kcal).
const double kcalPerLbMuscle = 2500;

/// Energy per gram of macronutrients.
const int kcalPerGramProtein = 4;
const int kcalPerGramCarb = 4;
const int kcalPerGramFat = 9;
const int kcalPerGramAlcohol = 7;

/// Kilograms → pounds.
const double kgToLb = 2.2046226218;

/// Pounds → kilograms.
const double lbToKg = 1 / kgToLb;

/// Centimeters → inches.
const double cmToIn = 1 / 2.54;

/// Centimeters → meters.
const double cmToM = 0.01;

/// Inches → centimeters.
const double inToCm = 2.54;

// === Energy + rate constants (§9.8) ===

/// Bulk daily surplus per kg of body weight per month (includes +50% NEAT buffer).
const double surplusKcalPerKgPerMonth = 330;

/// Cut daily deficit per kg of body weight per week.
const double deficitKcalPerKgPerWeek = 1100;

/// Bulk adjustment protocol: surplus per lb per month.
const double surplusKcalPerLbPerMonth = 150;

/// Cut adjustment protocol: deficit per lb per week.
const double deficitKcalPerLbPerWeek = 500;

/// Hard cap on cut rate (1.0% body weight / week).
const double maxWeeklyLossPct = 0.010;

/// Default cut rate when no tier and no BF% — 0.75% BW/week.
const double defaultCutRatePct = 0.0075;

/// "Sweet spot" cut rate (below bulk_start) — 0.5% BW/week.
const double sweetSpotCutRatePct = 0.005;

// === Macro constants (§9.9) ===

const int fatAbsoluteFloorG = 40;
const double fatPerLbFloor = 0.25;
const double saturatedFatCeilingPct = 0.10;
const double cutTargetWeightPctOfCurrent = 0.90;
const double proteinGPerCmHeightObese = 1.0;
const double veganProteinBoost = 1.20;
const double vegetarianProteinBoost = 1.10;

// Protein rules
const double proteinPerLbLbmCut = 1.14;
const double proteinPerLbLbmNonCut = 1.0;
const double proteinPerLbTargetWeightCutUnknownBf = 1.0;
const double proteinPerLbBodyWeightNonCutUnknownBf = 0.73;

// === Hydration constants (§9.10) ===

const int baseMlPerKg = 30;
const int sexAddMlMale = 300;
const int sweatRateLight = 300;
const int sweatRateModerate = 500;
const int sweatRateIntense = 800;
const double climateMultiplierCold = 0.95;
const double climateMultiplierTemperate = 1.0;
const double climateMultiplierHot = 1.3;
const double climateMultiplierHotHumid = 1.4;
const int pregnancyAddMl = 300;
const int breastfeedingAddMl = 700;
const double hydrationSoftCeilingL = 5.0;

// === Recipe scoring constants (§9.11) ===

const double minScale = 0.7;
const double maxScale = 1.5;
const double noScaleBand = 0.10;
const double scaleDeviationLimit = 0.40;
const double fillerThresholdKcal = 50;
const double fillerThresholdProteinG = 5;
const double fillerThresholdCarbG = 5;
const double fillerThresholdFatG = 3;
const double fillerThresholdFiberG = 3;
const double fillerServingCapProtein = 4;
const double fillerServingCapCarb = 3;
const double fillerServingCapFat = 3;
const double fillerMinServingFrac = 0.5;
const int vegMinG = 80;
const int vegMaxG = 200;
const int minAcceptableScore = 60;

// === Periodization (§9.12) ===

const double deloadSetsMultiplier = 0.5;
const double deloadRpeDelta = -1.5;

// === Helper functions ===

/// Convert kg → lb.
double kgToLbDouble(double kg) => kg * kgToLb;

/// Convert lb → kg.
double lbToKgDouble(double lb) => lb * lbToKg;

/// Convert cm → inches.
double cmToInches(double cm) => cm * cmToIn;

/// Convert cm → meters.
double cmToMeters(double cm) => cm * cmToM;

/// Compute lean body mass (kg) from weight (kg) and body fat percentage.
double leanBodyMassKg(double weightKg, double bfPct) =>
    weightKg * (1 - bfPct / 100);

/// Compute fat mass (kg) from weight (kg) and body fat percentage.
double fatMassKg(double weightKg, double bfPct) => weightKg * bfPct / 100;

/// BMI = weight (kg) / height (m)^2.
double bmi(double weightKg, double heightCm) {
  final h = cmToMeters(heightCm);
  return weightKg / (h * h);
}

/// Base-10 logarithm helper (Dart only has natural log natively).
double log10(double x) => math.log(x) / math.ln10;
