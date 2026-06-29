/// Nutrition plan output models. See spec §9.1 (output tree).
library;

import 'enums.dart';

class RMRResult {
  RMRResult({
    required this.formula,
    required this.baseRmrKcal,
    required this.metabolicAdaptationFactor,
    required this.weightReducedFactor,
    required this.adjustedRmrKcal,
    required this.notes,
  });

  final RMRFormula formula;
  final double baseRmrKcal;
  final double metabolicAdaptationFactor;
  final double weightReducedFactor;
  final double adjustedRmrKcal;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'formula': formula.toJson(),
        'base_rmr_kcal': baseRmrKcal,
        'metabolic_adaptation_factor': metabolicAdaptationFactor,
        'weight_reduced_factor': weightReducedFactor,
        'adjusted_rmr_kcal': adjustedRmrKcal,
        'notes': notes,
      };

  factory RMRResult.fromJson(Map<String, dynamic> json) {
    return RMRResult(
      formula: RMRFormulaJson.fromJson(json['formula'] as String),
      baseRmrKcal: (json['base_rmr_kcal'] as num).toDouble(),
      metabolicAdaptationFactor:
          (json['metabolic_adaptation_factor'] as num).toDouble(),
      weightReducedFactor:
          (json['weight_reduced_factor'] as num).toDouble(),
      adjustedRmrKcal: (json['adjusted_rmr_kcal'] as num).toDouble(),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class TDEEResult {
  TDEEResult({
    required this.rmrKcal,
    required this.activityFactor,
    required this.tdeeKcal,
    this.adaptiveTdeeKcal,
    required this.finalTdeeKcal,
    required this.notes,
  });

  final double rmrKcal;
  final double activityFactor;
  final double tdeeKcal;
  final double? adaptiveTdeeKcal;
  final double finalTdeeKcal;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'rmr_kcal': rmrKcal,
        'activity_factor': activityFactor,
        'tdee_kcal': tdeeKcal,
        'adaptive_tdee_kcal': adaptiveTdeeKcal,
        'final_tdee_kcal': finalTdeeKcal,
        'notes': notes,
      };

  factory TDEEResult.fromJson(Map<String, dynamic> json) {
    return TDEEResult(
      rmrKcal: (json['rmr_kcal'] as num).toDouble(),
      activityFactor: (json['activity_factor'] as num).toDouble(),
      tdeeKcal: (json['tdee_kcal'] as num).toDouble(),
      adaptiveTdeeKcal: (json['adaptive_tdee_kcal'] as num?)?.toDouble(),
      finalTdeeKcal: (json['final_tdee_kcal'] as num).toDouble(),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class CalorieTargets {
  CalorieTargets({
    required this.strategy,
    required this.baseTdeeKcal,
    required this.ratePct,
    required this.rateLabel,
    required this.calorieDeltaKcal,
    required this.targetCaloriesKcal,
    required this.calorieFloorApplied,
    this.floorKcal,
    required this.notes,
  });

  final CalorieStrategy strategy;
  final double baseTdeeKcal;
  final double ratePct;
  final String rateLabel;
  final double calorieDeltaKcal;
  final double targetCaloriesKcal;
  final bool calorieFloorApplied;
  final double? floorKcal;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'strategy': strategy.toJson(),
        'base_tdee_kcal': baseTdeeKcal,
        'rate_pct': ratePct,
        'rate_label': rateLabel,
        'calorie_delta_kcal': calorieDeltaKcal,
        'target_calories_kcal': targetCaloriesKcal,
        'calorie_floor_applied': calorieFloorApplied,
        'floor_kcal': floorKcal,
        'notes': notes,
      };

  factory CalorieTargets.fromJson(Map<String, dynamic> json) {
    return CalorieTargets(
      strategy: CalorieStrategyJson.fromJson(json['strategy'] as String),
      baseTdeeKcal: (json['base_tdee_kcal'] as num).toDouble(),
      ratePct: (json['rate_pct'] as num).toDouble(),
      rateLabel: json['rate_label'] as String,
      calorieDeltaKcal: (json['calorie_delta_kcal'] as num).toDouble(),
      targetCaloriesKcal: (json['target_calories_kcal'] as num).toDouble(),
      calorieFloorApplied: json['calorie_floor_applied'] as bool,
      floorKcal: (json['floor_kcal'] as num?)?.toDouble(),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class MacroSplit {
  MacroSplit({
    required this.proteinG,
    required this.fatG,
    required this.carbG,
    required this.proteinPct,
    required this.fatPct,
    required this.carbPct,
    required this.proteinKcal,
    required this.fatKcal,
    required this.carbKcal,
    required this.notes,
  });

  final double proteinG;
  final double fatG;
  final double carbG;
  final double proteinPct;
  final double fatPct;
  final double carbPct;
  final double proteinKcal;
  final double fatKcal;
  final double carbKcal;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'protein_g': proteinG,
        'fat_g': fatG,
        'carb_g': carbG,
        'protein_pct': proteinPct,
        'fat_pct': fatPct,
        'carb_pct': carbPct,
        'protein_kcal': proteinKcal,
        'fat_kcal': fatKcal,
        'carb_kcal': carbKcal,
        'notes': notes,
      };

  factory MacroSplit.fromJson(Map<String, dynamic> json) {
    return MacroSplit(
      proteinG: (json['protein_g'] as num).toDouble(),
      fatG: (json['fat_g'] as num).toDouble(),
      carbG: (json['carb_g'] as num).toDouble(),
      proteinPct: (json['protein_pct'] as num).toDouble(),
      fatPct: (json['fat_pct'] as num).toDouble(),
      carbPct: (json['carb_pct'] as num).toDouble(),
      proteinKcal: (json['protein_kcal'] as num).toDouble(),
      fatKcal: (json['fat_kcal'] as num).toDouble(),
      carbKcal: (json['carb_kcal'] as num).toDouble(),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class HydrationTarget {
  HydrationTarget({
    required this.waterLitersPerDay,
    required this.components,
    required this.notes,
  });

  final double waterLitersPerDay;
  final Map<String, double> components;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'water_liters_per_day': waterLitersPerDay,
        'components': components,
        'notes': notes,
      };

  factory HydrationTarget.fromJson(Map<String, dynamic> json) {
    return HydrationTarget(
      waterLitersPerDay: (json['water_liters_per_day'] as num).toDouble(),
      components: (json['components'] as Map).map(
          (k, v) => MapEntry(k as String, (v as num).toDouble())),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class MicronutrientTargets {
  MicronutrientTargets({
    required this.fiberG,
    required this.fruitCups,
    required this.vegCups,
    required this.notes,
  });

  final double fiberG;
  final int fruitCups;
  final int vegCups;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'fiber_g': fiberG,
        'fruit_cups': fruitCups,
        'veg_cups': vegCups,
        'notes': notes,
      };

  factory MicronutrientTargets.fromJson(Map<String, dynamic> json) {
    return MicronutrientTargets(
      fiberG: (json['fiber_g'] as num).toDouble(),
      fruitCups: (json['fruit_cups'] as num).toInt(),
      vegCups: (json['veg_cups'] as num).toInt(),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}

class NutritionPlan {
  NutritionPlan({
    required this.rmr,
    required this.tdee,
    required this.calories,
    required this.macros,
    required this.hydration,
    required this.micronutrients,
    required this.timelineWeeks,
    required this.notes,
  });

  final RMRResult rmr;
  final TDEEResult tdee;
  final CalorieTargets calories;
  final MacroSplit macros;
  final HydrationTarget hydration;
  final MicronutrientTargets micronutrients;
  final int timelineWeeks;
  final List<String> notes;

  Map<String, dynamic> toJson() => {
        'rmr': rmr.toJson(),
        'tdee': tdee.toJson(),
        'calories': calories.toJson(),
        'macros': macros.toJson(),
        'hydration': hydration.toJson(),
        'micronutrients': micronutrients.toJson(),
        'timeline_weeks': timelineWeeks,
        'notes': notes,
      };

  factory NutritionPlan.fromJson(Map<String, dynamic> json) {
    return NutritionPlan(
      rmr: RMRResult.fromJson(json['rmr'] as Map<String, dynamic>),
      tdee: TDEEResult.fromJson(json['tdee'] as Map<String, dynamic>),
      calories:
          CalorieTargets.fromJson(json['calories'] as Map<String, dynamic>),
      macros: MacroSplit.fromJson(json['macros'] as Map<String, dynamic>),
      hydration:
          HydrationTarget.fromJson(json['hydration'] as Map<String, dynamic>),
      micronutrients: MicronutrientTargets.fromJson(
          json['micronutrients'] as Map<String, dynamic>),
      timelineWeeks: (json['timeline_weeks'] as num).toInt(),
      notes: (json['notes'] as List).cast<String>(),
    );
  }
}
