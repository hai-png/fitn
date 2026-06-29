/// User profile model. See spec §4.1.2.
///
/// Construction-time validation throws [ArgumentError] with a clear message on
/// range violations and log-length mismatches.
library;

import 'enums.dart';
import '../utils/units.dart';

class UserProfile {
  UserProfile({
    required this.age,
    required this.sex,
    required this.heightCm,
    required this.weightKg,
    required this.activityLevel,
    required this.trainingStatus,
    required this.primaryGoal,
    required this.trainingDaysPerWeek,
    required this.equipmentAccess,
    this.dietType = DietType.omnivore,
    this.bodyFatPct,
    this.neckCm,
    this.waistCm,
    this.hipCm,
    this.cutRateTier,
    this.bulkAggressiveness,
    this.trainingTimeOfDay = TrainingTimeOfDay.evening,
    this.weightLogKg = const [],
    this.intakeLogKcal = const [],
  }) {
    // Range checks.
    if (age < 18 || age > 100) {
      throw ArgumentError('age must be 18–100, got $age');
    }
    if (heightCm < 140 || heightCm > 230) {
      throw ArgumentError('heightCm must be 140–230, got $heightCm');
    }
    if (weightKg < 35 || weightKg > 300) {
      throw ArgumentError('weightKg must be 35–300, got $weightKg');
    }
    if (trainingDaysPerWeek < 2 || trainingDaysPerWeek > 6) {
      throw ArgumentError(
          'trainingDaysPerWeek must be 2–6, got $trainingDaysPerWeek');
    }
    if (bodyFatPct != null && (bodyFatPct! < 2 || bodyFatPct! > 60)) {
      throw ArgumentError(
          'bodyFatPct must be 2–60 or null, got $bodyFatPct');
    }
    if (neckCm != null && (neckCm! < 20 || neckCm! > 80)) {
      throw ArgumentError('neckCm must be 20–80 or null, got $neckCm');
    }
    if (waistCm != null && (waistCm! < 40 || waistCm! > 200)) {
      throw ArgumentError('waistCm must be 40–200 or null, got $waistCm');
    }
    if (hipCm != null && (hipCm! < 40 || hipCm! > 200)) {
      throw ArgumentError('hipCm must be 40–200 or null, got $hipCm');
    }
    // Log validation.
    if (weightLogKg.length > 365) {
      throw ArgumentError(
          'weightLogKg.length must be ≤365, got ${weightLogKg.length}');
    }
    if (intakeLogKcal.length > 365) {
      throw ArgumentError(
          'intakeLogKcal.length must be ≤365, got ${intakeLogKcal.length}');
    }
    for (final w in weightLogKg) {
      if (w < 30 || w > 300) {
        throw ArgumentError(
            'weightLogKg entries must be 30–300, got $w');
      }
    }
    for (final k in intakeLogKcal) {
      if (k < 0 || k > 10000) {
        throw ArgumentError(
            'intakeLogKcal entries must be 0–10000, got $k');
      }
    }
    if (weightLogKg.isNotEmpty &&
        intakeLogKcal.isNotEmpty &&
        weightLogKg.length != intakeLogKcal.length) {
      throw ArgumentError(
          'weightLogKg.length (${weightLogKg.length}) must equal intakeLogKcal.length (${intakeLogKcal.length}) when both non-empty');
    }
  }

  final int age;
  final Sex sex;
  final double heightCm;
  final double weightKg;
  final ActivityLevel activityLevel;
  final TrainingStatus trainingStatus;
  final PrimaryGoal primaryGoal;
  final int trainingDaysPerWeek;
  final EquipmentAccess equipmentAccess;
  final DietType dietType;
  final double? bodyFatPct;
  final double? neckCm;
  final double? waistCm;
  final double? hipCm;
  final CutRateTier? cutRateTier;
  final BulkAggressiveness? bulkAggressiveness;
  final TrainingTimeOfDay trainingTimeOfDay;
  final List<double> weightLogKg;
  final List<double> intakeLogKcal;

  // === Computed getters ===

  double get bmi {
    final h = heightM;
    return weightKg / (h * h);
  }
  double get heightM => cmToMeters(heightCm);
  double get heightIn => cmToInches(heightCm);
  double get weightLb => weightKg * kgToLb;

  bool get hasCircumferenceMeasurements => switch (sex) {
        Sex.male => neckCm != null && waistCm != null,
        Sex.female => neckCm != null && waistCm != null && hipCm != null,
      };

  // === JSON ===

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      age: (json['age'] as num).toInt(),
      sex: SexJson.fromJson(json['sex'] as String),
      heightCm: (json['height_cm'] as num).toDouble(),
      weightKg: (json['weight_kg'] as num).toDouble(),
      activityLevel:
          ActivityLevelJson.fromJson(json['activity_level'] as String),
      trainingStatus:
          TrainingStatusJson.fromJson(json['training_status'] as String),
      primaryGoal: PrimaryGoalJson.fromJson(json['primary_goal'] as String),
      trainingDaysPerWeek: (json['training_days_per_week'] as num).toInt(),
      equipmentAccess:
          EquipmentAccessJson.fromJson(json['equipment_access'] as String),
      dietType: json['diet_type'] != null
          ? DietTypeJson.fromJson(json['diet_type'] as String)
          : DietType.omnivore,
      bodyFatPct: (json['body_fat_pct'] as num?)?.toDouble(),
      neckCm: (json['neck_cm'] as num?)?.toDouble(),
      waistCm: (json['waist_cm'] as num?)?.toDouble(),
      hipCm: (json['hip_cm'] as num?)?.toDouble(),
      cutRateTier: json['cut_rate_tier'] != null
          ? CutRateTierJson.fromJson(json['cut_rate_tier'] as String)
          : null,
      bulkAggressiveness: json['bulk_aggressiveness'] != null
          ? BulkAggressivenessJson.fromJson(
              json['bulk_aggressiveness'] as String)
          : null,
      trainingTimeOfDay: json['training_time_of_day'] != null
          ? TrainingTimeOfDayJson.fromJson(
              json['training_time_of_day'] as String)
          : TrainingTimeOfDay.evening,
      weightLogKg: (json['weight_log_kg'] as List<dynamic>? ?? [])
          .map((e) => (e as num).toDouble())
          .toList(),
      intakeLogKcal: (json['intake_log_kcal'] as List<dynamic>? ?? [])
          .map((e) => (e as num).toDouble())
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'age': age,
        'sex': sex.toJson(),
        'height_cm': heightCm,
        'weight_kg': weightKg,
        'activity_level': activityLevel.toJson(),
        'training_status': trainingStatus.toJson(),
        'primary_goal': primaryGoal.toJson(),
        'training_days_per_week': trainingDaysPerWeek,
        'equipment_access': equipmentAccess.toJson(),
        'diet_type': dietType.toJson(),
        'body_fat_pct': bodyFatPct,
        'neck_cm': neckCm,
        'waist_cm': waistCm,
        'hip_cm': hipCm,
        'cut_rate_tier': cutRateTier?.toJson(),
        'bulk_aggressiveness': bulkAggressiveness?.toJson(),
        'training_time_of_day': trainingTimeOfDay.toJson(),
        'weight_log_kg': weightLogKg,
        'intake_log_kcal': intakeLogKcal,
      };

  UserProfile copyWith({
    int? age,
    Sex? sex,
    double? heightCm,
    double? weightKg,
    ActivityLevel? activityLevel,
    TrainingStatus? trainingStatus,
    PrimaryGoal? primaryGoal,
    int? trainingDaysPerWeek,
    EquipmentAccess? equipmentAccess,
    DietType? dietType,
    Object? bodyFatPct = _sentinel,
    Object? neckCm = _sentinel,
    Object? waistCm = _sentinel,
    Object? hipCm = _sentinel,
    Object? cutRateTier = _sentinel,
    Object? bulkAggressiveness = _sentinel,
    TrainingTimeOfDay? trainingTimeOfDay,
    List<double>? weightLogKg,
    List<double>? intakeLogKcal,
  }) {
    return UserProfile(
      age: age ?? this.age,
      sex: sex ?? this.sex,
      heightCm: heightCm ?? this.heightCm,
      weightKg: weightKg ?? this.weightKg,
      activityLevel: activityLevel ?? this.activityLevel,
      trainingStatus: trainingStatus ?? this.trainingStatus,
      primaryGoal: primaryGoal ?? this.primaryGoal,
      trainingDaysPerWeek: trainingDaysPerWeek ?? this.trainingDaysPerWeek,
      equipmentAccess: equipmentAccess ?? this.equipmentAccess,
      dietType: dietType ?? this.dietType,
      bodyFatPct: identical(bodyFatPct, _sentinel) ? this.bodyFatPct : bodyFatPct as double?,
      neckCm: identical(neckCm, _sentinel) ? this.neckCm : neckCm as double?,
      waistCm: identical(waistCm, _sentinel) ? this.waistCm : waistCm as double?,
      hipCm: identical(hipCm, _sentinel) ? this.hipCm : hipCm as double?,
      cutRateTier: identical(cutRateTier, _sentinel)
          ? this.cutRateTier
          : cutRateTier as CutRateTier?,
      bulkAggressiveness: identical(bulkAggressiveness, _sentinel)
          ? this.bulkAggressiveness
          : bulkAggressiveness as BulkAggressiveness?,
      trainingTimeOfDay: trainingTimeOfDay ?? this.trainingTimeOfDay,
      weightLogKg: weightLogKg ?? this.weightLogKg,
      intakeLogKcal: intakeLogKcal ?? this.intakeLogKcal,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserProfile &&
          runtimeType == other.runtimeType &&
          age == other.age &&
          sex == other.sex &&
          heightCm == other.heightCm &&
          weightKg == other.weightKg &&
          activityLevel == other.activityLevel &&
          trainingStatus == other.trainingStatus &&
          primaryGoal == other.primaryGoal &&
          trainingDaysPerWeek == other.trainingDaysPerWeek &&
          equipmentAccess == other.equipmentAccess &&
          dietType == other.dietType &&
          bodyFatPct == other.bodyFatPct &&
          neckCm == other.neckCm &&
          waistCm == other.waistCm &&
          hipCm == other.hipCm &&
          cutRateTier == other.cutRateTier &&
          bulkAggressiveness == other.bulkAggressiveness &&
          trainingTimeOfDay == other.trainingTimeOfDay &&
          _listEq(weightLogKg, other.weightLogKg) &&
          _listEq(intakeLogKcal, other.intakeLogKcal);

  @override
  int get hashCode => Object.hash(
        age,
        sex,
        heightCm,
        weightKg,
        activityLevel,
        trainingStatus,
        primaryGoal,
        trainingDaysPerWeek,
        equipmentAccess,
        dietType,
        bodyFatPct,
        neckCm,
        waistCm,
        hipCm,
        cutRateTier,
        bulkAggressiveness,
        trainingTimeOfDay,
        Object.hashAll(weightLogKg),
        Object.hashAll(intakeLogKcal),
      );

  static bool _listEq(List<double> a, List<double> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }
}

const Object _sentinel = Object();
