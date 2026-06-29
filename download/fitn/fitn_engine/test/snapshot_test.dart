/// Smoke tests for fitn_engine.
///
/// Run with: `dart test` from the `fitn_engine/` directory.
library;

import 'package:test/test.dart';
import 'package:fitn_engine/fitn_engine.dart';

void main() {
  group('EngineData loading', () {
    test('loads all asset files successfully', () async {
      final data = await loadEngineData();
      expect(data.exercises.length, greaterThan(1000),
          reason: 'Should load 1,217+ exercises');
      expect(data.splits.length, equals(8),
          reason: 'Should load 8 split designs');
      expect(data.movementPatterns.length, greaterThan(30),
          reason: 'Should load 40 movement patterns');
      expect(data.recipes.length, greaterThan(200),
          reason: 'Should load curated + uncurated + pre/post recipes');
      expect(data.foodDatabase.length, greaterThan(20),
          reason: 'Should load ~30 foods');
    });
  });

  group('Assessment', () {
    late EngineData data;
    late FitnEngine engine;

    setUpAll(() async {
      data = await loadEngineData();
      engine = FitnEngine(data: data);
    });

    test('assesses a known profile as non-partial', () {
      final profile = UserProfile(
        age: 30,
        sex: Sex.male,
        heightCm: 180,
        weightKg: 80,
        activityLevel: ActivityLevel.lightlyActive,
        trainingStatus: TrainingStatus.novice,
        primaryGoal: PrimaryGoal.muscleGain,
        trainingDaysPerWeek: 4,
        equipmentAccess: EquipmentAccess.fullGym,
        bodyFatPct: 18,
      );
      final assessment = engine.assessProfile(profile);
      expect(assessment.isPartial, isFalse,
          reason: 'Errors: ${assessment.errors}');
      expect(assessment.bodyComposition, isNotNull);
      expect(assessment.bodyComposition!.bodyFatPct, closeTo(18, 0.1));
      expect(assessment.healthRisk, isNotNull);
      expect(assessment.muscularPotential, isNotNull);
      expect(assessment.recommendedStrategy, RecommendedStrategy.bulk);
    });

    test('uses Navy BF% when circumference measurements provided', () {
      final profile = UserProfile(
        age: 35,
        sex: Sex.male,
        heightCm: 178,
        weightKg: 85,
        activityLevel: ActivityLevel.mostlySedentary,
        trainingStatus: TrainingStatus.beginner,
        primaryGoal: PrimaryGoal.fatLoss,
        trainingDaysPerWeek: 3,
        equipmentAccess: EquipmentAccess.homeGym,
        neckCm: 38,
        waistCm: 95,
      );
      final assessment = engine.assessProfile(profile);
      expect(assessment.bodyComposition, isNotNull);
      expect(assessment.bodyComposition!.bodyFatMethod,
          BodyFatMethod.navy);
    });

    test('falls back to CUN-BAE when no measurements', () {
      final profile = UserProfile(
        age: 28,
        sex: Sex.female,
        heightCm: 165,
        weightKg: 70,
        activityLevel: ActivityLevel.lightlyActive,
        trainingStatus: TrainingStatus.novice,
        primaryGoal: PrimaryGoal.recomp,
        trainingDaysPerWeek: 4,
        equipmentAccess: EquipmentAccess.fullGym,
      );
      final assessment = engine.assessProfile(profile);
      expect(assessment.bodyComposition, isNotNull);
      expect(assessment.bodyComposition!.bodyFatMethod,
          BodyFatMethod.cunBae);
    });
  });

  group('Plan generation', () {
    late FitnEngine engine;

    setUpAll(() async {
      final data = await loadEngineData();
      engine = FitnEngine(data: data);
    });

    test('generates a complete plan for a novice male bulking', () async {
      final profile = UserProfile(
        age: 26,
        sex: Sex.male,
        heightCm: 180,
        weightKg: 75,
        activityLevel: ActivityLevel.active,
        trainingStatus: TrainingStatus.novice,
        primaryGoal: PrimaryGoal.muscleGain,
        trainingDaysPerWeek: 4,
        equipmentAccess: EquipmentAccess.fullGym,
        bodyFatPct: 14,
      );
      final prefs = PlanPreferences(
        mealFrequency: 4,
        cuisinePreference: 'mediterranean',
      );
      final response = engine.generatePlan(profile, prefs);

      expect(response.plan.engineVersion, equals('3.2.0'));
      expect(response.assessment.isPartial, isFalse);
      expect(response.plan.nutrition.calories.targetCaloriesKcal,
          greaterThan(1500));
      expect(response.plan.training.mesocycles, isNotEmpty);
      expect(response.plan.meal.days, hasLength(7));
      expect(response.plan.summary, contains('3.2.0'));
    });

    test('generates a plan for an obese beginner (habit change)', () {
      final profile = UserProfile(
        age: 40,
        sex: Sex.male,
        heightCm: 175,
        weightKg: 110,
        activityLevel: ActivityLevel.sedentary,
        trainingStatus: TrainingStatus.beginner,
        primaryGoal: PrimaryGoal.muscleGain,
        trainingDaysPerWeek: 3,
        equipmentAccess: EquipmentAccess.bodyweightOnly,
        bodyFatPct: 30,
      );
      final prefs = PlanPreferences(mealFrequency: 3);
      // Should not throw — should produce a habitChangeFirst or cut plan.
      final response = engine.generatePlan(profile, prefs);
      expect(response.assessment.recommendedStrategy,
          anyOf(equals(RecommendedStrategy.cut),
              equals(RecommendedStrategy.habitChangeFirst)));
      expect(response.plan.meal.days, hasLength(7));
    });

    test('round-trips JSON correctly', () {
      final profile = UserProfile(
        age: 30,
        sex: Sex.female,
        heightCm: 165,
        weightKg: 60,
        activityLevel: ActivityLevel.lightlyActive,
        trainingStatus: TrainingStatus.intermediate,
        primaryGoal: PrimaryGoal.strength,
        trainingDaysPerWeek: 5,
        equipmentAccess: EquipmentAccess.fullGym,
        bodyFatPct: 22,
      );
      final prefs = PlanPreferences(mealFrequency: 3);
      final response = engine.generatePlan(profile, prefs);

      final json = response.plan.toJson();
      final restored = FitnessPlan.fromJson(json);
      expect(restored.engineVersion, equals(response.plan.engineVersion));
      expect(restored.nutrition.calories.targetCaloriesKcal,
          equals(response.plan.nutrition.calories.targetCaloriesKcal));
      expect(restored.training.splitType,
          equals(response.plan.training.splitType));
      expect(restored.meal.days.length,
          equals(response.plan.meal.days.length));
    });
  });

  group('Edge cases', () {
    late FitnEngine engine;

    setUpAll(() async {
      final data = await loadEngineData();
      engine = FitnEngine(data: data);
    });

    test('handles very tall + very heavy profile', () {
      final profile = UserProfile(
        age: 25,
        sex: Sex.male,
        heightCm: 210,
        weightKg: 130,
        activityLevel: ActivityLevel.active,
        trainingStatus: TrainingStatus.intermediate,
        primaryGoal: PrimaryGoal.muscleGain,
        trainingDaysPerWeek: 5,
        equipmentAccess: EquipmentAccess.fullGym,
        bodyFatPct: 18,
      );
      final prefs = PlanPreferences(mealFrequency: 4);
      final response = engine.generatePlan(profile, prefs);
      expect(response.plan.meal.days, hasLength(7));
    });

    test('handles very short + very light profile', () {
      final profile = UserProfile(
        age: 22,
        sex: Sex.female,
        heightCm: 145,
        weightKg: 42,
        activityLevel: ActivityLevel.lightlyActive,
        trainingStatus: TrainingStatus.beginner,
        primaryGoal: PrimaryGoal.muscleGain,
        trainingDaysPerWeek: 3,
        equipmentAccess: EquipmentAccess.bodyweightOnly,
        bodyFatPct: 18,
      );
      final prefs = PlanPreferences(mealFrequency: 3);
      final response = engine.generatePlan(profile, prefs);
      expect(response.plan.meal.days, hasLength(7));
    });

    test('handles empty logs', () {
      final profile = UserProfile(
        age: 30,
        sex: Sex.male,
        heightCm: 180,
        weightKg: 80,
        activityLevel: ActivityLevel.active,
        trainingStatus: TrainingStatus.novice,
        primaryGoal: PrimaryGoal.maintenance,
        trainingDaysPerWeek: 4,
        equipmentAccess: EquipmentAccess.fullGym,
        bodyFatPct: 16,
      );
      final prefs = PlanPreferences(mealFrequency: 3);
      final response = engine.generatePlan(profile, prefs);
      expect(response.plan.nutrition.tdee.adaptiveTdeeKcal, isNull,
          reason: 'No logs → no adaptive TDEE');
    });

    test('handles max-length logs (365 days)', () {
      final weightLog = List<double>.generate(365, (i) => 80 + i * 0.01);
      final intakeLog = List<double>.filled(365, 2500);
      final profile = UserProfile(
        age: 30,
        sex: Sex.male,
        heightCm: 180,
        weightKg: 80,
        activityLevel: ActivityLevel.active,
        trainingStatus: TrainingStatus.novice,
        primaryGoal: PrimaryGoal.maintenance,
        trainingDaysPerWeek: 4,
        equipmentAccess: EquipmentAccess.fullGym,
        bodyFatPct: 16,
        weightLogKg: weightLog,
        intakeLogKcal: intakeLog,
      );
      final prefs = PlanPreferences(mealFrequency: 3);
      final response = engine.generatePlan(profile, prefs);
      expect(response.plan.meal.days, hasLength(7));
    });
  });

  group('Banker\'s rounding', () {
    test('rounds half-to-even', () {
      expect(round1(0.5), equals(0));
      expect(round1(1.5), equals(2));
      expect(round1(2.5), equals(2));
      expect(round1(3.5), equals(4));
      expect(round2(0.125), equals(0.12));
      expect(round2(0.135), equals(0.14));
    });

    test('roundBankersToInt', () {
      expect(roundBankersToInt(0.5), equals(0));
      expect(roundBankersToInt(1.5), equals(2));
      expect(roundBankersToInt(2.5), equals(2));
    });
  });

  group('Allergen scanning', () {
    test('coconut milk does NOT match dairy allergen', () {
      final hasAllergen = containsAllergen(
          '1 cup coconut milk, 2 tbsp olive oil', ['dairy']);
      expect(hasAllergen, isFalse,
          reason: 'coconut milk must NOT match dairy (plant qualifier)');
    });

    test('regular milk DOES match dairy allergen', () {
      final hasAllergen = containsAllergen(
          '1 cup whole milk, 2 tbsp olive oil', ['dairy']);
      expect(hasAllergen, isTrue);
    });

    test('eggplant does NOT match eggs allergen', () {
      final hasAllergen =
          containsAllergen('1 medium eggplant, sliced', ['eggs']);
      expect(hasAllergen, isFalse);
    });

    test('actual eggs DO match eggs allergen', () {
      final hasAllergen =
          containsAllergen('2 eggs, scrambled', ['eggs']);
      expect(hasAllergen, isTrue);
    });

    test('almond milk does NOT match dairy', () {
      final hasAllergen =
          containsAllergen('1 cup almond milk', ['dairy']);
      expect(hasAllergen, isFalse);
    });

    test('peanut butter matches peanuts allergen', () {
      final hasAllergen =
          containsAllergen('2 tbsp peanut butter', ['peanuts']);
      expect(hasAllergen, isTrue);
    });

    test('tree_nuts alias normalizes to nuts', () {
      expect(normalizeAllergen('tree_nuts'), equals('nuts'));
      expect(normalizeAllergen('crustacean'), equals('shellfish'));
    });
  });
}
