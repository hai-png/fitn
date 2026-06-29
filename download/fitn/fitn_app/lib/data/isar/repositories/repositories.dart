/// In-memory repositories for all collections. See spec §5.1.
///
/// In a production build these would use Isar. For this skeleton we use simple
/// in-memory storage that persists to SharedPreferences as JSON. This makes
/// the app immediately runnable without Isar codegen, while keeping the
/// repository API identical so a real Isar swap is mechanical.
library;

import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

import 'collections/collections.dart';

class _LocalStorage {
  static SharedPreferences? _prefs;
  static Future<SharedPreferences> get prefs async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs!;
  }

  static Future<String?> read(String key) async => (await prefs).getString(key);
  static Future<void> write(String key, String value) async =>
      (await prefs).setString(key, value);
  static Future<void> remove(String key) async => (await prefs).remove(key);
}

class ProfileRepository {
  static const _key = 'fitn_profile';
  ProfileRecord? _cache;

  Future<ProfileRecord?> get() async {
    if (_cache != null) return _cache;
    final s = await _LocalStorage.read(_key);
    if (s == null) return null;
    _cache = ProfileRecord.fromJson(jsonDecode(s) as Map<String, dynamic>);
    return _cache;
  }

  Future<void> put(ProfileRecord r) async {
    r.updatedAt = DateTime.now();
    if (r.syncStatus == 'synced') r.syncStatus = 'pending';
    _cache = r;
    await _LocalStorage.write(_key, jsonEncode(r.toJson()));
  }

  Future<void> clear() async {
    _cache = null;
    await _LocalStorage.remove(_key);
  }
}

class PlanRepository {
  static const _key = 'fitn_plans';

  List<PlanRecord> _cache = [];

  Future<List<PlanRecord>> all() async {
    if (_cache.isNotEmpty) return _cache;
    final s = await _LocalStorage.read(_key);
    if (s == null) return [];
    final list = jsonDecode(s) as List;
    _cache = list
        .map((e) => PlanRecord.fromJson(e as Map<String, dynamic>))
        .toList();
    return _cache;
  }

  Future<PlanRecord?> getActive() async {
    final all = await this.all();
    return all.where((p) => p.isActive).firstOrNull;
  }

  Future<void> put(PlanRecord r) async {
    if (r.syncStatus == 'synced') r.syncStatus = 'pending';
    final all = await this.all();
    final idx = all.indexWhere((p) => p.planId == r.planId);
    if (idx >= 0) {
      all[idx] = r;
    } else {
      all.add(r);
    }
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> deactivateAll() async {
    final all = await this.all();
    for (final p in all) {
      if (p.isActive) {
        p.isActive = false;
        p.syncStatus = 'pending';
      }
    }
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> remove(String planId) async {
    final all = await this.all();
    all.removeWhere((p) => p.planId == planId);
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }
}

class WorkoutLogRepository {
  static const _key = 'fitn_workout_logs';

  List<WorkoutLogRecord> _cache = [];

  Future<List<WorkoutLogRecord>> all() async {
    if (_cache.isNotEmpty) return _cache;
    final s = await _LocalStorage.read(_key);
    if (s == null) return [];
    final list = jsonDecode(s) as List;
    _cache = list
        .map((e) => WorkoutLogRecord.fromJson(e as Map<String, dynamic>))
        .toList();
    return _cache;
  }

  Future<List<WorkoutLogRecord>> forPlan(String planId) async {
    final all = await this.all();
    return all.where((w) => w.planId == planId).toList()
      ..sort((a, b) => b.startedAt.compareTo(a.startedAt));
  }

  Future<void> put(WorkoutLogRecord r) async {
    if (r.syncStatus == 'synced') r.syncStatus = 'pending';
    final all = await this.all();
    if (r.id != null) {
      final idx = all.indexWhere((e) => e.id == r.id);
      if (idx >= 0) {
        all[idx] = r;
      } else {
        r.id = all.isEmpty ? 1 : all.last.id! + 1;
        all.add(r);
      }
    } else {
      r.id = all.isEmpty ? 1 : all.last.id! + 1;
      all.add(r);
    }
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }
}

class WeightLogRepository {
  static const _key = 'fitn_weight_logs';

  List<WeightLogRecord> _cache = [];

  Future<List<WeightLogRecord>> all() async {
    if (_cache.isNotEmpty) return _cache;
    final s = await _LocalStorage.read(_key);
    if (s == null) return [];
    final list = jsonDecode(s) as List;
    _cache = list
        .map((e) => WeightLogRecord.fromJson(e as Map<String, dynamic>))
        .toList();
    return _cache;
  }

  Future<void> put(WeightLogRecord r) async {
    if (r.syncStatus == 'synced') r.syncStatus = 'pending';
    final all = await this.all();
    final idx = all.indexWhere((e) => e.date.isSameDay(r.date));
    if (idx >= 0) {
      all[idx] = r;
    } else {
      all.add(r);
    }
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> clear() async {
    _cache = [];
    await _LocalStorage.remove(_key);
  }
}

class IntakeLogRepository {
  static const _key = 'fitn_intake_logs';

  List<IntakeLogRecord> _cache = [];

  Future<List<IntakeLogRecord>> all() async {
    if (_cache.isNotEmpty) return _cache;
    final s = await _LocalStorage.read(_key);
    if (s == null) return [];
    final list = jsonDecode(s) as List;
    _cache = list
        .map((e) => IntakeLogRecord.fromJson(e as Map<String, dynamic>))
        .toList();
    return _cache;
  }

  Future<void> put(IntakeLogRecord r) async {
    if (r.syncStatus == 'synced') r.syncStatus = 'pending';
    final all = await this.all();
    final idx = all.indexWhere((e) => e.date.isSameDay(r.date));
    if (idx >= 0) {
      all[idx] = r;
    } else {
      all.add(r);
    }
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> clear() async {
    _cache = [];
    await _LocalStorage.remove(_key);
  }
}

class SyncQueueRepository {
  static const _key = 'fitn_sync_queue';

  List<SyncQueueRecord> _cache = [];

  Future<List<SyncQueueRecord>> pending() async {
    final all = await _all();
    return all.where((e) => e.status == 'pending').toList();
  }

  Future<List<SyncQueueRecord>> _all() async {
    if (_cache.isNotEmpty) return _cache;
    final s = await _LocalStorage.read(_key);
    if (s == null) return [];
    final list = jsonDecode(s) as List;
    _cache = list
        .map((e) => SyncQueueRecord.fromJson(e as Map<String, dynamic>))
        .toList();
    return _cache;
  }

  Future<void> enqueue(SyncQueueRecord r) async {
    final all = await _all();
    r.id = all.isEmpty ? 1 : all.last.id! + 1;
    all.add(r);
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> markInProgress(int id) async {
    final all = await _all();
    final idx = all.indexWhere((e) => e.id == id);
    if (idx >= 0) all[idx].status = 'in_progress';
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> markSynced(int id) async {
    final all = await _all();
    all.removeWhere((e) => e.id == id);
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> markFailed(int id, {Duration? backoff}) async {
    final all = await _all();
    final idx = all.indexWhere((e) => e.id == id);
    if (idx >= 0) {
      all[idx].status = 'pending';
      all[idx].attempts++;
      all[idx].nextAttemptAt =
          DateTime.now().add(backoff ?? const Duration(minutes: 1));
    }
    _cache = all;
    await _LocalStorage.write(
        _key, jsonEncode(all.map((e) => e.toJson()).toList()));
  }

  Future<void> clear() async {
    _cache = [];
    await _LocalStorage.remove(_key);
  }

  Future<int> count() async => (await pending()).length;
}
