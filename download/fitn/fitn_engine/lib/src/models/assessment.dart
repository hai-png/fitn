/// Assessment output models. See spec §9.1 (output tree).
library;

import 'enums.dart';

class BodyComposition {
  BodyComposition({
    required this.bodyFatPct,
    required this.bodyFatMethod,
    required this.bodyFatCategory,
    required this.leanBodyMassKg,
    required this.fatMassKg,
    required this.bmi,
    required this.bmiCategory,
    required this.ffmi,
    required this.normalizedFfmi,
    required this.targetWeightsKg,
    required this.notes,
  });

  final double bodyFatPct;
  final BodyFatMethod bodyFatMethod;
  final BodyFatCategory bodyFatCategory;
  final double leanBodyMassKg;
  final double fatMassKg;
  final double bmi;
  final BMICategory bmiCategory;
  final double ffmi;
  final double normalizedFfmi;
  final Map<String, double> targetWeightsKg; // {athletic, fitness, acceptable, hormonal_floor}
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'body_fat_pct': bodyFatPct,
        'body_fat_method': bodyFatMethod.toJson(),
        'body_fat_category': bodyFatCategory.toJson(),
        'lean_body_mass_kg': leanBodyMassKg,
        'fat_mass_kg': fatMassKg,
        'bmi': bmi,
        'bmi_category': bmiCategory.toJson(),
        'ffmi': ffmi,
        'normalized_ffmi': normalizedFfmi,
        'target_weights_kg': targetWeightsKg,
        'notes': notes,
      };

  factory BodyComposition.fromJson(Map<String, dynamic> json) {
    return BodyComposition(
      bodyFatPct: (json['body_fat_pct'] as num).toDouble(),
      bodyFatMethod:
          BodyFatMethodJson.fromJson(json['body_fat_method'] as String),
      bodyFatCategory:
          BodyFatCategoryJson.fromJson(json['body_fat_category'] as String),
      leanBodyMassKg: (json['lean_body_mass_kg'] as num).toDouble(),
      fatMassKg: (json['fat_mass_kg'] as num).toDouble(),
      bmi: (json['bmi'] as num).toDouble(),
      bmiCategory: BMICategoryJson.fromJson(json['bmi_category'] as String),
      ffmi: (json['ffmi'] as num).toDouble(),
      normalizedFfmi: (json['normalized_ffmi'] as num).toDouble(),
      targetWeightsKg: (json['target_weights_kg'] as Map).map(
          (k, v) => MapEntry(k as String, (v as num).toDouble())),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class HealthRiskAssessment {
  HealthRiskAssessment({
    required this.whr,
    required this.whrRisk,
    required this.whtr,
    required this.whtrRisk,
    required this.absi,
    required this.absiZScore,
    required this.absiRisk,
    required this.ibwDevineKg,
    required this.ibwRobinsonKg,
    required this.ibwMillerKg,
    required this.ibwHamwiKg,
    required this.overallRisk,
    required this.riskFactors,
    required this.notes,
  });

  final double? whr;
  final HealthRiskLevel? whrRisk;
  final double? whtr;
  final HealthRiskLevel? whtrRisk;
  final double? absi;
  final double? absiZScore;
  final ABSIRiskLevel? absiRisk;
  final double? ibwDevineKg;
  final double? ibwRobinsonKg;
  final double? ibwMillerKg;
  final double? ibwHamwiKg;
  final HealthRiskLevel overallRisk;
  final List<String> riskFactors;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'whr': whr,
        'whr_risk': whrRisk?.toJson(),
        'whtr': whtr,
        'whtr_risk': whtrRisk?.toJson(),
        'absi': absi,
        'absi_z_score': absiZScore,
        'absi_risk': absiRisk?.toJson(),
        'ibw_devine_kg': ibwDevineKg,
        'ibw_robinson_kg': ibwRobinsonKg,
        'ibw_miller_kg': ibwMillerKg,
        'ibw_hamwi_kg': ibwHamwiKg,
        'overall_risk': overallRisk.toJson(),
        'risk_factors': riskFactors,
        'notes': notes,
      };

  factory HealthRiskAssessment.fromJson(Map<String, dynamic> json) {
    return HealthRiskAssessment(
      whr: (json['whr'] as num?)?.toDouble(),
      whrRisk: json['whr_risk'] != null
          ? HealthRiskLevelJson.fromJson(json['whr_risk'] as String)
          : null,
      whtr: (json['whtr'] as num?)?.toDouble(),
      whtrRisk: json['whtr_risk'] != null
          ? HealthRiskLevelJson.fromJson(json['whtr_risk'] as String)
          : null,
      absi: (json['absi'] as num?)?.toDouble(),
      absiZScore: (json['absi_z_score'] as num?)?.toDouble(),
      absiRisk: json['absi_risk'] != null
          ? ABSIRiskLevelJson.fromJson(json['absi_risk'] as String)
          : null,
      ibwDevineKg: (json['ibw_devine_kg'] as num?)?.toDouble(),
      ibwRobinsonKg: (json['ibw_robinson_kg'] as num?)?.toDouble(),
      ibwMillerKg: (json['ibw_miller_kg'] as num?)?.toDouble(),
      ibwHamwiKg: (json['ibw_hamwi_kg'] as num?)?.toDouble(),
      overallRisk:
          HealthRiskLevelJson.fromJson(json['overall_risk'] as String),
      riskFactors: (json['risk_factors'] as List).cast<String>(),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class MuscularPotential {
  MuscularPotential({
    required this.currentFfmi,
    required this.currentNormalizedFfmi,
    required this.naturalCeilingFfmi,
    required this.attainableCeilingFfmi,
    required this.likelyMaxFfmi,
    required this.berkhanStageMaxKg,
    required this.ffmiToCeilingPct,
    required this.headroomKg,
    required this.expectedMonthlyMuscleGainKg,
    required this.isAboveCeiling,
    required this.notes,
  });

  final double currentFfmi;
  final double currentNormalizedFfmi;
  final double naturalCeilingFfmi;
  final double attainableCeilingFfmi;
  final double likelyMaxFfmi;
  final double? berkhanStageMaxKg;
  final double ffmiToCeilingPct;
  final double headroomKg;
  final double expectedMonthlyMuscleGainKg;
  final bool isAboveCeiling;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'current_ffmi': currentFfmi,
        'current_normalized_ffmi': currentNormalizedFfmi,
        'natural_ceiling_ffmi': naturalCeilingFfmi,
        'attainable_ceiling_ffmi': attainableCeilingFfmi,
        'likely_max_ffmi': likelyMaxFfmi,
        'berkhan_stage_max_kg': berkhanStageMaxKg,
        'ffmi_to_ceiling_pct': ffmiToCeilingPct,
        'headroom_kg': headroomKg,
        'expected_monthly_muscle_gain_kg': expectedMonthlyMuscleGainKg,
        'is_above_ceiling': isAboveCeiling,
        'notes': notes,
      };

  factory MuscularPotential.fromJson(Map<String, dynamic> json) {
    return MuscularPotential(
      currentFfmi: (json['current_ffmi'] as num).toDouble(),
      currentNormalizedFfmi:
          (json['current_normalized_ffmi'] as num).toDouble(),
      naturalCeilingFfmi:
          (json['natural_ceiling_ffmi'] as num).toDouble(),
      attainableCeilingFfmi:
          (json['attainable_ceiling_ffmi'] as num).toDouble(),
      likelyMaxFfmi: (json['likely_max_ffmi'] as num).toDouble(),
      berkhanStageMaxKg: (json['berkhan_stage_max_kg'] as num?)?.toDouble(),
      ffmiToCeilingPct:
          (json['ffmi_to_ceiling_pct'] as num).toDouble(),
      headroomKg: (json['headroom_kg'] as num).toDouble(),
      expectedMonthlyMuscleGainKg:
          (json['expected_monthly_muscle_gain_kg'] as num).toDouble(),
      isAboveCeiling: json['is_above_ceiling'] as bool,
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class AssessmentResult {
  AssessmentResult({
    required this.bodyComposition,
    required this.healthRisk,
    required this.muscularPotential,
    required this.recommendedStrategy,
    required this.strategyRationale,
    required this.summary,
    required this.isPartial,
    required this.errors,
  });

  final BodyComposition? bodyComposition;
  final HealthRiskAssessment? healthRisk;
  final MuscularPotential? muscularPotential;
  final RecommendedStrategy recommendedStrategy;
  final String strategyRationale;
  final String summary;
  final bool isPartial;
  final List<String> errors;

  Map<String, dynamic> toJson() => {
        'body_composition': bodyComposition?.toJson(),
        'health_risk': healthRisk?.toJson(),
        'muscular_potential': muscularPotential?.toJson(),
        'recommended_strategy': recommendedStrategy.toJson(),
        'strategy_rationale': strategyRationale,
        'summary': summary,
        'is_partial': isPartial,
        'errors': errors,
      };

  factory AssessmentResult.fromJson(Map<String, dynamic> json) {
    return AssessmentResult(
      bodyComposition: json['body_composition'] != null
          ? BodyComposition.fromJson(
              json['body_composition'] as Map<String, dynamic>)
          : null,
      healthRisk: json['health_risk'] != null
          ? HealthRiskAssessment.fromJson(
              json['health_risk'] as Map<String, dynamic>)
          : null,
      muscularPotential: json['muscular_potential'] != null
          ? MuscularPotential.fromJson(
              json['muscular_potential'] as Map<String, dynamic>)
          : null,
      recommendedStrategy: RecommendedStrategyJson.fromJson(
          json['recommended_strategy'] as String),
      strategyRationale: json['strategy_rationale'] as String,
      summary: json['summary'] as String,
      isPartial: json['is_partial'] as bool,
      errors: (json['errors'] as List).cast<String>(),
    );
  }
}
