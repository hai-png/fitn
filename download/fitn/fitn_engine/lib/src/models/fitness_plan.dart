/// Top-level FitnessPlan container + GeneratePlanResponse. See spec §9.1.
library;

import 'assessment.dart';
import 'meal.dart';
import 'nutrition.dart';
import 'training.dart';
import '../version.dart';

import '../models/profile.dart';
import '../models/preferences.dart';

class FitnessPlan {
  FitnessPlan({
    required this.nutrition,
    required this.training,
    required this.meal,
    required this.summary,
    required this.engineVersion,
  });

  final NutritionPlan nutrition;
  final TrainingPlan training;
  final MealPlan meal;
  final String summary;
  final String engineVersion;

  Map<String, dynamic> toJson() => {
        'nutrition': nutrition.toJson(),
        'training': training.toJson(),
        'meal': meal.toJson(),
        'summary': summary,
        'engine_version': engineVersion,
      };

  factory FitnessPlan.fromJson(Map<String, dynamic> json) {
    return FitnessPlan(
      nutrition:
          NutritionPlan.fromJson(json['nutrition'] as Map<String, dynamic>),
      training:
          TrainingPlan.fromJson(json['training'] as Map<String, dynamic>),
      meal: MealPlan.fromJson(json['meal'] as Map<String, dynamic>),
      summary: json['summary'] as String,
      engineVersion: json['engine_version'] as String? ?? engineVersion,
    );
  }
}

class GeneratePlanResponse {
  GeneratePlanResponse({
    required this.profile,
    required this.preferences,
    required this.assessment,
    required this.plan,
  });

  final UserProfile profile;
  final PlanPreferences preferences;
  final AssessmentResult assessment;
  final FitnessPlan plan;

  Map<String, dynamic> toJson() => {
        'profile': profile.toJson(),
        'preferences': preferences.toJson(),
        'assessment': assessment.toJson(),
        'plan': plan.toJson(),
      };

  factory GeneratePlanResponse.fromJson(Map<String, dynamic> json) {
    return GeneratePlanResponse(
      profile:
          UserProfile.fromJson(json['profile'] as Map<String, dynamic>),
      preferences: PlanPreferences.fromJson(
          json['preferences'] as Map<String, dynamic>),
      assessment: AssessmentResult.fromJson(
          json['assessment'] as Map<String, dynamic>),
      plan: FitnessPlan.fromJson(json['plan'] as Map<String, dynamic>),
    );
  }
}
