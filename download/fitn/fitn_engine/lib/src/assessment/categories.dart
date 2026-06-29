/// BMI + body fat category bands. See spec §4.2.2 and §4.2.3.
library;

import '../models/enums.dart';

/// Classify BMI. See §4.2.2.
BMICategory bmiCategory(double bmi) {
  if (bmi < 18.5) return BMICategory.underweight;
  if (bmi < 25.0) return BMICategory.normal;
  if (bmi < 30.0) return BMICategory.overweight;
  return BMICategory.obese;
}

/// Classify body fat percentage (sex-specific). See §4.2.3.
BodyFatCategory bodyFatCategory(double bfPct, Sex sex) {
  if (sex == Sex.male) {
    if (bfPct < 6) return BodyFatCategory.essential;
    if (bfPct < 14) return BodyFatCategory.athlete;
    if (bfPct < 18) return BodyFatCategory.fitness;
    if (bfPct < 25) return BodyFatCategory.acceptable;
    return BodyFatCategory.obesity;
  } else {
    if (bfPct < 14) return BodyFatCategory.essential;
    if (bfPct < 21) return BodyFatCategory.athlete;
    if (bfPct < 25) return BodyFatCategory.fitness;
    if (bfPct < 32) return BodyFatCategory.acceptable;
    return BodyFatCategory.obesity;
  }
}
