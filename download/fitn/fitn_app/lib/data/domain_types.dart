/// Additional domain types ported from fitness-app.
///
/// Marketplace products, meal-ordering products, cart items, orders, water
/// logs, and exercise set logs (for advanced analytics).
library;

import 'collections.dart';

class MealProduct {
  MealProduct({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.image,
    required this.category,
  });
  final String id;
  final String name;
  final String description;
  final double price;
  final int calories;
  final int protein;
  final int carbs;
  final int fat;
  final String image;
  final String category; // "high-protein" | "low-carb" | "keto" | "vegetarian" | "vegan" | "balanced"

  factory MealProduct.fromJson(Map<String, dynamic> j) => MealProduct(
        id: j['id'] as String,
        name: j['name'] as String,
        description: j['description'] as String,
        price: (j['price'] as num).toDouble(),
        calories: (j['calories'] as num).toInt(),
        protein: (j['protein'] as num).toInt(),
        carbs: (j['carbs'] as num).toInt(),
        fat: (j['fat'] as num).toInt(),
        image: j['image'] as String,
        category: j['category'] as String,
      );
}

class MarketplaceProduct {
  MarketplaceProduct({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    required this.rating,
    required this.image,
    required this.category,
    this.badge,
  });
  final String id;
  final String name;
  final String description;
  final double price;
  final double rating;
  final String image;
  final String category; // "supplements" | "equipment" | "apparel" | "accessories"
  final String? badge;

  factory MarketplaceProduct.fromJson(Map<String, dynamic> j) =>
      MarketplaceProduct(
        id: j['id'] as String,
        name: j['name'] as String,
        description: j['description'] as String,
        price: (j['price'] as num).toDouble(),
        rating: (j['rating'] as num).toDouble(),
        image: j['image'] as String,
        category: j['category'] as String,
        badge: j['badge'] as String?,
      );
}

class CartItem {
  CartItem({
    required this.id,
    required this.name,
    required this.price,
    required this.image,
    required this.quantity,
    required this.type,
  });
  final String id;
  final String name;
  final double price;
  final String image;
  final int quantity;
  final String type; // "meal" | "marketplace"

  CartItem copyWith({int? quantity}) => CartItem(
        id: id,
        name: name,
        price: price,
        image: image,
        quantity: quantity ?? this.quantity,
        type: type,
      );
}

class Order {
  Order({
    required this.id,
    required this.items,
    required this.total,
    required this.date,
    required this.status,
    required this.deliveryAddress,
  });
  final String id;
  final List<CartItem> items;
  final double total;
  final String date;
  final String status; // "pending" | "processing" | "shipped" | "delivered"
  final String deliveryAddress;
}

class WaterLog {
  WaterLog({required this.date, required this.amountMl});
  final DateTime date;
  final int amountMl;
}

/// A single set logged by the user.
class ExerciseSetLog {
  ExerciseSetLog({
    required this.id,
    required this.weight,
    required this.reps,
    this.isWarmUp = false,
    this.type = 'Normal',
  });
  final String id;
  final double weight;
  final int reps;
  final bool isWarmUp;
  final String type; // "Normal" | "AMRAP" | "Failure" | "Drop Set"

  double get volume => isWarmUp ? 0 : weight * reps;
}

/// A single exercise session (multiple sets) logged on a given date.
class ExerciseLog {
  ExerciseLog({
    required this.id,
    required this.exerciseName,
    required this.targetMuscle,
    required this.date,
    required this.sets,
    required this.durationMinutes,
  });
  final String id;
  final String exerciseName;
  final String targetMuscle;
  final DateTime date;
  final List<ExerciseSetLog> sets;
  final int durationMinutes;
}

/// A logged workout (top-level summary).
class WorkoutLogSummary {
  WorkoutLogSummary({
    required this.date,
    required this.workoutTitle,
    required this.durationMinutes,
    required this.caloriesBurned,
  });
  final DateTime date;
  final String workoutTitle;
  final int durationMinutes;
  final int caloriesBurned;
}

/// Lifetime volume tier — gamification for total tonnage lifted.
class LifetimeTier {
  const LifetimeTier({
    required this.name,
    required this.minTons,
    required this.maxTons,
  });
  final String name;
  final double minTons;
  final double maxTons;
}

const List<LifetimeTier> lifetimeTiers = [
  LifetimeTier(name: 'Novice', minTons: 0, maxTons: 5),
  LifetimeTier(name: 'Apprentice', minTons: 5, maxTons: 25),
  LifetimeTier(name: 'Adept', minTons: 25, maxTons: 100),
  LifetimeTier(name: 'Veteran', minTons: 100, maxTons: 250),
  LifetimeTier(name: 'Master', minTons: 250, maxTons: 500),
  LifetimeTier(name: 'Legend', minTons: 500, maxTons: 1000),
  LifetimeTier(name: 'Mythic', minTons: 1000, maxTons: 100000),
];

/// Muscle volume zone (per muscle group).
class MuscleVolumeZone {
  MuscleVolumeZone({
    required this.muscle,
    required this.totalVolumeKg,
    required this.balancePct,
    required this.zone,
  });
  final String muscle;
  final double totalVolumeKg;
  final double balancePct;
  final String zone; // "MEV" | "MAV" | "MRV" | "ML"
}

/// Personal record (1RM or max weight × reps for an exercise).
class PersonalRecord {
  PersonalRecord({
    required this.exerciseName,
    required this.estimated1Rm,
    required this.weight,
    required this.reps,
    required this.date,
  });
  final String exerciseName;
  final double estimated1Rm;
  final double weight;
  final int reps;
  final DateTime date;
}
