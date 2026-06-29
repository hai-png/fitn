/// Isar collections. See spec §5.1.
///
/// NOTE: The actual Isar `@Collection()` annotations are NOT used here because
/// generating Isar schemas requires `isar_generator` (build_runner) which we
/// don't run in this skeleton. Instead, these are plain Dart classes that
/// mirror the spec'd schema. A real build will run `dart run build_runner
/// build` to generate Isar bindings.
///
/// For persistence, we serialize to JSON and store in Isar as strings (a
/// "typed KV" approach) — exactly as the spec describes for `dataJson` fields.
/// This works without codegen and gives us full query power on the indexed
/// columns.
library;

import 'dart:convert';

class ProfileRecord {
  ProfileRecord({
    this.id = 1, // singleton
    required this.userId,
    required this.dataJson,
    required this.updatedAt,
    required this.syncStatus,
  });

  int id;
  String userId;
  String dataJson;
  DateTime updatedAt;
  String syncStatus; // "pending" | "synced" | "conflict"

  Map<String, dynamic> get data => jsonDecode(dataJson) as Map<String, dynamic>;
  set data(Map<String, dynamic> v) => dataJson = jsonEncode(v);

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'data_json': dataJson,
        'updated_at': updatedAt.toIso8601String(),
        'sync_status': syncStatus,
      };

  factory ProfileRecord.fromJson(Map<String, dynamic> json) {
    return ProfileRecord(
      id: (json['id'] as num?)?.toInt() ?? 1,
      userId: json['user_id'] as String,
      dataJson: json['data_json'] as String,
      updatedAt: DateTime.parse(json['updated_at'] as String),
      syncStatus: json['sync_status'] as String,
    );
  }
}

class PlanRecord {
  PlanRecord({
    this.id,
    required this.userId,
    required this.planId,
    required this.dataJson,
    required this.profileSnapshotJson,
    required this.preferencesSnapshotJson,
    required this.engineVersion,
    required this.isActive,
    required this.generatedAt,
    required this.syncStatus,
  });

  int? id;
  String userId;
  String planId;
  String dataJson;
  String profileSnapshotJson;
  String preferencesSnapshotJson;
  String engineVersion;
  bool isActive;
  DateTime generatedAt;
  String syncStatus;

  Map<String, dynamic> get data => jsonDecode(dataJson) as Map<String, dynamic>;
  set data(Map<String, dynamic> v) => dataJson = jsonEncode(v);

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'plan_id': planId,
        'data_json': dataJson,
        'profile_snapshot_json': profileSnapshotJson,
        'preferences_snapshot_json': preferencesSnapshotJson,
        'engine_version': engineVersion,
        'is_active': isActive,
        'generated_at': generatedAt.toIso8601String(),
        'sync_status': syncStatus,
      };

  factory PlanRecord.fromJson(Map<String, dynamic> json) {
    return PlanRecord(
      id: (json['id'] as num?)?.toInt(),
      userId: json['user_id'] as String,
      planId: json['plan_id'] as String,
      dataJson: json['data_json'] as String,
      profileSnapshotJson: json['profile_snapshot_json'] as String,
      preferencesSnapshotJson: json['preferences_snapshot_json'] as String,
      engineVersion: json['engine_version'] as String,
      isActive: json['is_active'] as bool,
      generatedAt: DateTime.parse(json['generated_at'] as String),
      syncStatus: json['sync_status'] as String,
    );
  }
}

class SetEntry {
  SetEntry({
    required this.exerciseSlug,
    required this.setNum,
    this.weightKg,
    this.reps,
    this.rpe,
    required this.done,
    required this.completedAt,
  });

  String exerciseSlug;
  int setNum;
  double? weightKg;
  int? reps;
  double? rpe;
  bool done;
  DateTime completedAt;

  Map<String, dynamic> toJson() => {
        'exercise_slug': exerciseSlug,
        'set_num': setNum,
        'weight_kg': weightKg,
        'reps': reps,
        'rpe': rpe,
        'done': done,
        'completed_at': completedAt.toIso8601String(),
      };

  factory SetEntry.fromJson(Map<String, dynamic> json) {
    return SetEntry(
      exerciseSlug: json['exercise_slug'] as String,
      setNum: (json['set_num'] as num).toInt(),
      weightKg: (json['weight_kg'] as num?)?.toDouble(),
      reps: (json['reps'] as num?)?.toInt(),
      rpe: (json['rpe'] as num?)?.toDouble(),
      done: json['done'] as bool,
      completedAt: DateTime.parse(json['completed_at'] as String),
    );
  }
}

class WorkoutLogRecord {
  WorkoutLogRecord({
    this.id,
    required this.userId,
    required this.planId,
    required this.dayNumber,
    required this.startedAt,
    this.completedAt,
    required this.workoutName,
    required this.dataJson,
    required this.syncStatus,
  });

  int? id;
  String userId;
  String planId;
  int dayNumber;
  DateTime startedAt;
  DateTime? completedAt;
  String workoutName;
  String dataJson; // JSON-encoded List<SetEntry>
  String syncStatus;

  List<SetEntry> get sets => (jsonDecode(dataJson) as List)
      .map((e) => SetEntry.fromJson(e as Map<String, dynamic>))
      .toList();
  set sets(List<SetEntry> v) =>
      dataJson = jsonEncode(v.map((e) => e.toJson()).toList());

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'plan_id': planId,
        'day_number': dayNumber,
        'started_at': startedAt.toIso8601String(),
        'completed_at': completedAt?.toIso8601String(),
        'workout_name': workoutName,
        'data_json': dataJson,
        'sync_status': syncStatus,
      };

  factory WorkoutLogRecord.fromJson(Map<String, dynamic> json) {
    return WorkoutLogRecord(
      id: (json['id'] as num?)?.toInt(),
      userId: json['user_id'] as String,
      planId: json['plan_id'] as String,
      dayNumber: (json['day_number'] as num).toInt(),
      startedAt: DateTime.parse(json['started_at'] as String),
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
      workoutName: json['workout_name'] as String,
      dataJson: json['data_json'] as String,
      syncStatus: json['sync_status'] as String,
    );
  }
}

class WeightLogRecord {
  WeightLogRecord({
    this.id,
    required this.userId,
    required this.date,
    required this.weightKg,
    required this.syncStatus,
  });

  int? id;
  String userId;
  DateTime date;
  double weightKg;
  String syncStatus;

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'date': date.ymd,
        'weight_kg': weightKg,
        'sync_status': syncStatus,
      };

  factory WeightLogRecord.fromJson(Map<String, dynamic> json) {
    return WeightLogRecord(
      id: (json['id'] as num?)?.toInt(),
      userId: json['user_id'] as String,
      date: DateTime.parse(json['date'] as String),
      weightKg: (json['weight_kg'] as num).toDouble(),
      syncStatus: json['sync_status'] as String,
    );
  }
}

class IntakeLogRecord {
  IntakeLogRecord({
    this.id,
    required this.userId,
    required this.date,
    required this.intakeKcal,
    required this.syncStatus,
  });

  int? id;
  String userId;
  DateTime date;
  double intakeKcal;
  String syncStatus;

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'date': date.ymd,
        'intake_kcal': intakeKcal,
        'sync_status': syncStatus,
      };

  factory IntakeLogRecord.fromJson(Map<String, dynamic> json) {
    return IntakeLogRecord(
      id: (json['id'] as num?)?.toInt(),
      userId: json['user_id'] as String,
      date: DateTime.parse(json['date'] as String),
      intakeKcal: (json['intake_kcal'] as num).toDouble(),
      syncStatus: json['sync_status'] as String,
    );
  }
}

class AppStateRecord {
  AppStateRecord({
    this.id = 1,
    required this.activeTab,
    required this.hasOnboarded,
    required this.planStale,
    this.activePlanId,
  });

  int id;
  String activeTab;
  bool hasOnboarded;
  bool planStale;
  String? activePlanId;

  Map<String, dynamic> toJson() => {
        'id': id,
        'active_tab': activeTab,
        'has_onboarded': hasOnboarded,
        'plan_stale': planStale,
        'active_plan_id': activePlanId,
      };

  factory AppStateRecord.fromJson(Map<String, dynamic> json) {
    return AppStateRecord(
      id: (json['id'] as num?)?.toInt() ?? 1,
      activeTab: json['active_tab'] as String? ?? 'home',
      hasOnboarded: json['has_onboarded'] as bool? ?? false,
      planStale: json['plan_stale'] as bool? ?? false,
      activePlanId: json['active_plan_id'] as String?,
    );
  }
}

class SyncQueueRecord {
  SyncQueueRecord({
    this.id,
    required this.operationType,
    required this.recordId,
    required this.collectionName,
    required this.attempts,
    this.nextAttemptAt,
    required this.status,
  });

  int? id;
  String operationType;
  String recordId;
  String collectionName;
  int attempts;
  DateTime? nextAttemptAt;
  String status; // "pending" | "in_progress" | "failed"

  Map<String, dynamic> toJson() => {
        'id': id,
        'operation_type': operationType,
        'record_id': recordId,
        'collection_name': collectionName,
        'attempts': attempts,
        'next_attempt_at': nextAttemptAt?.toIso8601String(),
        'status': status,
      };

  factory SyncQueueRecord.fromJson(Map<String, dynamic> json) {
    return SyncQueueRecord(
      id: (json['id'] as num?)?.toInt(),
      operationType: json['operation_type'] as String,
      recordId: json['record_id'] as String,
      collectionName: json['collection_name'] as String,
      attempts: (json['attempts'] as num?)?.toInt() ?? 0,
      nextAttemptAt: json['next_attempt_at'] != null
          ? DateTime.parse(json['next_attempt_at'] as String)
          : null,
      status: json['status'] as String? ?? 'pending',
    );
  }
}
