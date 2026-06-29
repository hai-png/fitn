/// All engine enums. See spec §4.1.1.
///
/// Wire form is snake_case (e.g. `"mostly_sedentary"`); in-Dart names are
/// camelCase. Helpers in `utils/enum_helpers.dart` bridge the two.
library;

import '../utils/enum_helpers.dart';

// === Inputs ===

enum Sex {
  male,
  female,
}

enum ActivityLevel {
  sedentary,
  mostlySedentary,
  lightlyActive,
  active,
  highlyActive,
}

enum TrainingStatus {
  beginner,
  novice,
  intermediate,
  advanced,
}

enum PrimaryGoal {
  fatLoss,
  muscleGain,
  recomp,
  maintenance,
  strength,
}

enum EquipmentAccess {
  fullGym,
  homeGym,
  bodyweightOnly,
}

enum DietType {
  omnivore,
  vegetarian,
  vegan,
}

enum CutRateTier {
  veryConservative,
  conservative,
  moderate,
  aggressive,
  veryAggressive,
}

enum BulkAggressiveness {
  conservative,
  happyMedium,
  aggressive,
  veryAggressive,
}

enum TrainingTimeOfDay {
  morning,
  midday,
  evening,
}

enum ExerciseIntensity {
  light,
  moderate,
  intense,
}

enum Climate {
  cold,
  temperate,
  hot,
  hotHumid,
}

// === Assessment ===

enum BodyFatMethod {
  userProvided,
  navy,
  cunBae,
}

enum BodyFatCategory {
  essential,
  athlete,
  fitness,
  acceptable,
  obesity,
}

enum BMICategory {
  underweight,
  normal,
  overweight,
  obese,
}

enum HealthRiskLevel {
  low,
  moderate,
  high,
  veryHigh,
}

enum ABSIRiskLevel {
  low,
  belowAverage,
  average,
  aboveAverage,
  high,
}

enum RecommendedStrategy {
  cut,
  bulk,
  recomp,
  maintenance,
  habitChangeFirst,
  reverseDiet,
}

// === Nutrition ===

enum RMRFormula {
  mifflinStJeor,
  harrisBenedictOriginal,
  harrisBenedictRevised,
  cunningham,
  katchMcArdle,
}

enum CalorieStrategy {
  deficit,
  surplus,
  maintenance,
  recomp,
  reverseDiet,
}

// === Training ===

enum TrainingGoal {
  strength,
  hypertrophy,
  generalFitness,
  fatLoss,
  muscleGain,
  recomp,
  maintenance,
}

enum SplitType {
  fullBody,
  upperLower,
  ppl,
  pplX2,
  pushPullLegsUpperLower,
  bodyPart,
  pushPull,
}

enum ProgressionScheme {
  linear,
  dup,
  block,
}

enum ExerciseCategory {
  compoundPrimary,
  compoundSecondary,
  accessory,
  cardio,
  mobility,
}

enum ExperienceLevel {
  beginner,
  intermediate,
  advanced,
}

// === Meal ===

enum MealType {
  breakfast,
  lunch,
  dinner,
  snack,
  side,
  preWorkout,
  postWorkout,
}

enum RecipeDietTag {
  omni,
  vegan,
  veganEthiopian,
  vegetarian,
  omniEthiopian,
}

enum FoodCategory {
  proteinAnimal,
  proteinPlant,
  dairy,
  carbGrain,
  carbStarchyVeg,
  carbFruit,
  fatOil,
  fatNutSeed,
  vegetable,
  beverage,
}

// === JSON helpers attached to each enum ===
//
// Each enum has a `fromJson` static and `toJson` instance method.
// Generate them by hand for each (small boilerplate).

extension SexJson on Sex {
  String toJson() => enumToJson(this);
  static Sex fromJson(String s) => enumFromString(Sex.values, s);
  String get display => enumToDisplay(this);
}

extension ActivityLevelJson on ActivityLevel {
  String toJson() => enumToJson(this);
  static ActivityLevel fromJson(String s) =>
      enumFromString(ActivityLevel.values, s);
  String get display => enumToDisplay(this);

  /// RippedBody activity factor (1.25 / 1.45 / 1.65 / 1.85 / 2.05).
  double get activityFactor => switch (this) {
        ActivityLevel.sedentary => 1.25,
        ActivityLevel.mostlySedentary => 1.45,
        ActivityLevel.lightlyActive => 1.65,
        ActivityLevel.active => 1.85,
        ActivityLevel.highlyActive => 2.05,
      };
}

extension TrainingStatusJson on TrainingStatus {
  String toJson() => enumToJson(this);
  static TrainingStatus fromJson(String s) =>
      enumFromString(TrainingStatus.values, s);
  String get display => enumToDisplay(this);
}

extension PrimaryGoalJson on PrimaryGoal {
  String toJson() => enumToJson(this);
  static PrimaryGoal fromJson(String s) =>
      enumFromString(PrimaryGoal.values, s);
  String get display => enumToDisplay(this);
}

extension EquipmentAccessJson on EquipmentAccess {
  String toJson() => enumToJson(this);
  static EquipmentAccess fromJson(String s) =>
      enumFromString(EquipmentAccess.values, s);
  String get display => enumToDisplay(this);
}

extension DietTypeJson on DietType {
  String toJson() => enumToJson(this);
  static DietType fromJson(String s) => enumFromString(DietType.values, s);
  String get display => enumToDisplay(this);
}

extension CutRateTierJson on CutRateTier {
  String toJson() => enumToJson(this);
  static CutRateTier fromJson(String s) =>
      enumFromString(CutRateTier.values, s);
  String get display => enumToDisplay(this);

  /// Cut rate tier → % BW/week. Hard cap 1.0% is enforced downstream.
  double get ratePct => switch (this) {
        CutRateTier.veryConservative => 0.005,
        CutRateTier.conservative => 0.0075,
        CutRateTier.moderate => 0.010,
        CutRateTier.aggressive => 0.010, // capped
        CutRateTier.veryAggressive => 0.010, // capped
      };
}

extension BulkAggressivenessJson on BulkAggressiveness {
  String toJson() => enumToJson(this);
  static BulkAggressiveness fromJson(String s) =>
      enumFromString(BulkAggressiveness.values, s);
  String get display => enumToDisplay(this);
}

extension TrainingTimeOfDayJson on TrainingTimeOfDay {
  String toJson() => enumToJson(this);
  static TrainingTimeOfDay fromJson(String s) =>
      enumFromString(TrainingTimeOfDay.values, s);
  String get display => enumToDisplay(this);
}

extension ExerciseIntensityJson on ExerciseIntensity {
  String toJson() => enumToJson(this);
  static ExerciseIntensity fromJson(String s) =>
      enumFromString(ExerciseIntensity.values, s);
  String get display => enumToDisplay(this);

  /// Sweat rate in mL/hr (light 300, moderate 500, intense 800).
  int get sweatRateMlPerHour => switch (this) {
        ExerciseIntensity.light => 300,
        ExerciseIntensity.moderate => 500,
        ExerciseIntensity.intense => 800,
      };
}

extension ClimateJson on Climate {
  String toJson() => enumToJson(this);
  static Climate fromJson(String s) => enumFromString(Climate.values, s);
  String get display => enumToDisplay(this);

  /// Climate multiplier applied to exercise component of hydration.
  double get multiplier => switch (this) {
        Climate.cold => 0.95,
        Climate.temperate => 1.0,
        Climate.hot => 1.3,
        Climate.hotHumid => 1.4,
      };
}

extension BodyFatMethodJson on BodyFatMethod {
  String toJson() => enumToJson(this);
  static BodyFatMethod fromJson(String s) =>
      enumFromString(BodyFatMethod.values, s);
  String get display => enumToDisplay(this);
}

extension BodyFatCategoryJson on BodyFatCategory {
  String toJson() => enumToJson(this);
  static BodyFatCategory fromJson(String s) =>
      enumFromString(BodyFatCategory.values, s);
  String get display => enumToDisplay(this);
}

extension BMICategoryJson on BMICategory {
  String toJson() => enumToJson(this);
  static BMICategory fromJson(String s) =>
      enumFromString(BMICategory.values, s);
  String get display => enumToDisplay(this);
}

extension HealthRiskLevelJson on HealthRiskLevel {
  String toJson() => enumToJson(this);
  static HealthRiskLevel fromJson(String s) =>
      enumFromString(HealthRiskLevel.values, s);
  String get display => enumToDisplay(this);
}

extension ABSIRiskLevelJson on ABSIRiskLevel {
  String toJson() => enumToJson(this);
  static ABSIRiskLevel fromJson(String s) =>
      enumFromString(ABSIRiskLevel.values, s);
  String get display => enumToDisplay(this);
}

extension RecommendedStrategyJson on RecommendedStrategy {
  String toJson() => enumToJson(this);
  static RecommendedStrategy fromJson(String s) =>
      enumFromString(RecommendedStrategy.values, s);
  String get display => enumToDisplay(this);
}

extension RMRFormulaJson on RMRFormula {
  String toJson() => enumToJson(this);
  static RMRFormula fromJson(String s) =>
      enumFromString(RMRFormula.values, s);
  String get display => enumToDisplay(this);
}

extension CalorieStrategyJson on CalorieStrategy {
  String toJson() => enumToJson(this);
  static CalorieStrategy fromJson(String s) =>
      enumFromString(CalorieStrategy.values, s);
  String get display => enumToDisplay(this);
}

extension TrainingGoalJson on TrainingGoal {
  String toJson() => enumToJson(this);
  static TrainingGoal fromJson(String s) =>
      enumFromString(TrainingGoal.values, s);
  String get display => enumToDisplay(this);
}

extension SplitTypeJson on SplitType {
  String toJson() => enumToJson(this);
  static SplitType fromJson(String s) => enumFromString(SplitType.values, s);
  String get display => enumToDisplay(this);
}

extension ProgressionSchemeJson on ProgressionScheme {
  String toJson() => enumToJson(this);
  static ProgressionScheme fromJson(String s) =>
      enumFromString(ProgressionScheme.values, s);
  String get display => enumToDisplay(this);
}

extension ExerciseCategoryJson on ExerciseCategory {
  String toJson() => enumToJson(this);
  static ExerciseCategory fromJson(String s) =>
      enumFromString(ExerciseCategory.values, s);
  String get display => enumToDisplay(this);
}

extension ExperienceLevelJson on ExperienceLevel {
  String toJson() => enumToJson(this);
  static ExperienceLevel fromJson(String s) =>
      enumFromString(ExperienceLevel.values, s);
  String get display => enumToDisplay(this);
}

extension MealTypeJson on MealType {
  String toJson() => enumToJson(this);
  static MealType fromJson(String s) => enumFromString(MealType.values, s);
  String get display => enumToDisplay(this);

  String get emoji => switch (this) {
        MealType.breakfast => '🌅',
        MealType.lunch => '☀️',
        MealType.dinner => '🌙',
        MealType.snack => '🍎',
        MealType.side => '🥗',
        MealType.preWorkout => '⚡',
        MealType.postWorkout => '🔋',
      };
}

extension RecipeDietTagJson on RecipeDietTag {
  String toJson() => enumToJson(this);
  static RecipeDietTag fromJson(String s) =>
      enumFromString(RecipeDietTag.values, s);
  String get display => enumToDisplay(this);

  /// Wire form uses SCREAMING_SNAKE (e.g. `"OMNI_ETHIOPIAN"`).
  String toJsonScreaming() => camelToSnake(name).toUpperCase();
  static RecipeDietTag fromJsonScreaming(String s) {
    final camel = snakeToCamel(s.toLowerCase());
    for (final v in RecipeDietTag.values) {
      if (v.name == camel) return v;
    }
    throw ArgumentError('Unknown RecipeDietTag: "$s"');
  }
}

extension FoodCategoryJson on FoodCategory {
  String toJson() => enumToJson(this);
  static FoodCategory fromJson(String s) =>
      enumFromString(FoodCategory.values, s);
  String get display => enumToDisplay(this);
}
