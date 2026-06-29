/// App state + Riverpod notifiers. See spec §6.3.
///
/// Single AppState class + fine-grained `select()` subscriptions.
library;

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../data/isar/collections/collections.dart';
import '../data/isar/repositories/repositories.dart';
import '../data/supabase/sync/sync_service.dart';
import '../engine/engine_provider.dart';

// === Tab enum ===

enum Tab { home, workouts, meals, progress, profile }

// === Auth state ===

class AuthState {
  const AuthState({
    this.session,
    this.status = AuthStatus.anonymous,
    this.email,
  });
  final Session? session;
  final AuthStatus status;
  final String? email;

  bool get isAuthenticated => status == AuthStatus.authenticated;
  String get userId => session?.user.id ?? 'anonymous';
}

enum AuthStatus { anonymous, authenticated }

// === App state ===

class AppState {
  const AppState({
    this.hydrated = false,
    this.hasOnboarded = false,
    this.activeTab = Tab.home,
    this.planGenerating = false,
    this.planError,
    this.planStale = false,
    this.profile,
    this.preferences,
    this.activePlan,
    this.activePlanId,
    this.planHistory = const [],
    this.auth,
    this.syncQueueLength = 0,
    this.lastSyncAt,
  });

  final bool hydrated;
  final bool hasOnboarded;
  final Tab activeTab;
  final bool planGenerating;
  final String? planError;
  final bool planStale;
  final UserProfile? profile;
  final PlanPreferences? preferences;
  final FitnessPlan? activePlan;
  final String? activePlanId;
  final List<PlanRecord> planHistory;
  final AuthState? auth;
  final int syncQueueLength;
  final DateTime? lastSyncAt;

  bool get hasPlan => activePlan != null;

  AppState copyWith({
    bool? hydrated,
    bool? hasOnboarded,
    Tab? activeTab,
    bool? planGenerating,
    String? planError,
    bool? planStale,
    UserProfile? profile,
    PlanPreferences? preferences,
    FitnessPlan? activePlan,
    String? activePlanId,
    List<PlanRecord>? planHistory,
    AuthState? auth,
    int? syncQueueLength,
    DateTime? lastSyncAt,
  }) {
    return AppState(
      hydrated: hydrated ?? this.hydrated,
      hasOnboarded: hasOnboarded ?? this.hasOnboarded,
      activeTab: activeTab ?? this.activeTab,
      planGenerating: planGenerating ?? this.planGenerating,
      planError: planError,
      planStale: planStale ?? this.planStale,
      profile: profile ?? this.profile,
      preferences: preferences ?? this.preferences,
      activePlan: activePlan ?? this.activePlan,
      activePlanId: activePlanId ?? this.activePlanId,
      planHistory: planHistory ?? this.planHistory,
      auth: auth ?? this.auth,
      syncQueueLength: syncQueueLength ?? this.syncQueueLength,
      lastSyncAt: lastSyncAt ?? this.lastSyncAt,
    );
  }
}

// === Providers ===

final profileRepoProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository();
});

final planRepoProvider = Provider<PlanRepository>((ref) {
  return PlanRepository();
});

final workoutLogRepoProvider = Provider<WorkoutLogRepository>((ref) {
  return WorkoutLogRepository();
});

final weightLogRepoProvider = Provider<WeightLogRepository>((ref) {
  return WeightLogRepository();
});

final intakeLogRepoProvider = Provider<IntakeLogRepository>((ref) {
  return IntakeLogRepository();
});

// === App notifier ===

final appNotifierProvider =
    AsyncNotifierProvider<AppNotifier, AppState>(AppNotifier.new);

class AppNotifier extends AsyncNotifier<AppState> {
  late final ProfileRepository _profileRepo;
  late final PlanRepository _planRepo;

  @override
  Future<AppState> build() async {
    _profileRepo = ref.watch(profileRepoProvider);
    _planRepo = ref.watch(planRepoProvider);

    // Hydrate from local storage.
    final profileRecord = await _profileRepo.get();
    final activePlan = await _planRepo.getActive();
    final allPlans = await _planRepo.all();

    UserProfile? profile;
    PlanPreferences? prefs;
    if (profileRecord != null) {
      final data = profileRecord.data;
      try {
        profile = UserProfile.fromJson(
            data['profile'] as Map<String, dynamic>);
      } catch (_) {}
      try {
        prefs = PlanPreferences.fromJson(
            data['preferences'] as Map<String, dynamic>);
      } catch (_) {}
    }

    FitnessPlan? plan;
    if (activePlan != null) {
      try {
        plan = FitnessPlan.fromJson(activePlan.data);
      } catch (_) {}
    }

    return AppState(
      hydrated: true,
      hasOnboarded: profile != null && plan != null,
      profile: profile,
      preferences: prefs,
      activePlan: plan,
      activePlanId: activePlan?.planId,
      planHistory: allPlans,
    );
  }

  Future<void> setActiveTab(Tab tab) async {
    state = AsyncData(state.value!.copyWith(activeTab: tab));
  }

  Future<void> setProfile(UserProfile p) async {
    final record = await _profileRepo.get() ??
        ProfileRecord(
          userId: 'anonymous',
          dataJson: '{}',
          updatedAt: DateTime.now(),
          syncStatus: 'pending',
        );
    record
      ..userId = state.value?.auth?.userId ?? 'anonymous'
      ..data = {
        'profile': p.toJson(),
        'preferences': state.value?.preferences?.toJson() ?? const {},
      };
    await _profileRepo.put(record);
    state = AsyncData(state.value!.copyWith(
      profile: p,
      planStale: true,
    ));
    await _enqueueSync('upsert_profile', record.id.toString(), 'ProfileRecord');
  }

  Future<void> setPreferences(PlanPreferences p) async {
    final record = await _profileRepo.get() ??
        ProfileRecord(
          userId: 'anonymous',
          dataJson: '{}',
          updatedAt: DateTime.now(),
          syncStatus: 'pending',
        );
    record
      ..userId = state.value?.auth?.userId ?? 'anonymous'
      ..data = {
        'profile': state.value?.profile?.toJson() ?? const {},
        'preferences': p.toJson(),
      };
    await _profileRepo.put(record);
    state = AsyncData(state.value!.copyWith(
      preferences: p,
      planStale: true,
    ));
    await _enqueueSync('upsert_profile', record.id.toString(), 'ProfileRecord');
  }

  Future<void> generatePlan() async {
    if (state.value!.planGenerating) return;
    final profile = state.value!.profile;
    final prefs = state.value!.preferences;
    if (profile == null || prefs == null) {
      state = AsyncData(state.value!.copyWith(
          planError: 'Profile or preferences missing'));
      return;
    }
    state = AsyncData(state.value!.copyWith(
      planGenerating: true,
      planError: null,
    ));
    try {
      final engineData = await getEngineData();
      final response = await generatePlanResponseInIsolate(
        profile: profile,
        prefs: prefs,
        engineData: engineData,
      );

      // Persist: deactivate old active plan, save new as active.
      await _planRepo.deactivateAll();
      final planId = DateTime.now().microsecondsSinceEpoch.toString();
      final planRecord = PlanRecord(
        userId: state.value?.auth?.userId ?? 'anonymous',
        planId: planId,
        dataJson: '{}',
        profileSnapshotJson: '{}',
        preferencesSnapshotJson: '{}',
        engineVersion: response.plan.engineVersion,
        isActive: true,
        generatedAt: DateTime.now(),
        syncStatus: 'pending',
      )
        ..data = response.plan.toJson()
        ..profileSnapshotJson = jsonEncode(profile.toJson())
        ..preferencesSnapshotJson = jsonEncode(prefs.toJson());
      await _planRepo.put(planRecord);
      final allPlans = await _planRepo.all();

      state = AsyncData(state.value!.copyWith(
        hasOnboarded: true,
        planStale: false,
        activePlan: response.plan,
        activePlanId: planId,
        planHistory: allPlans,
        planGenerating: false,
        activeTab: Tab.home,
      ));
      await _enqueueSync('upsert_plan', planId, 'PlanRecord');
    } on PartialAssessmentError catch (e) {
      state = AsyncData(state.value!.copyWith(
        planGenerating: false,
        planError: e.message,
      ));
    } catch (e) {
      state = AsyncData(state.value!.copyWith(
        planGenerating: false,
        planError: e.toString(),
      ));
    }
  }

  Future<void> restorePlan(String planId) async {
    final all = await _planRepo.all();
    final plan = all.where((p) => p.planId == planId).firstOrNull;
    if (plan == null) return;
    await _planRepo.deactivateAll();
    plan.isActive = true;
    plan.syncStatus = 'pending';
    await _planRepo.put(plan);
    FitnessPlan? fitnessPlan;
    try {
      fitnessPlan = FitnessPlan.fromJson(plan.data);
    } catch (_) {}
    state = AsyncData(state.value!.copyWith(
      activePlan: fitnessPlan,
      activePlanId: planId,
      planHistory: all,
    ));
    await _enqueueSync('upsert_plan', planId, 'PlanRecord');
  }

  Future<void> clearOnSignOut() async {
    // Reset auth state, keep local plan/profile/logs, clear sync queue.
    final sync = ref.read(syncProvider.notifier);
    await sync.clearQueue();
    state = AsyncData(state.value!.copyWith(
      auth: null,
      syncQueueLength: 0,
    ));
  }

  Future<void> setAuth(AuthState auth) async {
    state = AsyncData(state.value!.copyWith(auth: auth));
  }

  Future<void> _enqueueSync(
      String op, String recordId, String collection) async {
    final sync = ref.read(syncProvider.notifier);
    await sync.enqueue(
      operationType: op,
      recordId: recordId,
      collectionName: collection,
    );
    state = AsyncData(state.value!.copyWith(
      syncQueueLength: ref.read(syncProvider).queueLength,
      lastSyncAt: ref.read(syncProvider).lastSyncAt,
    ));
  }
}

// === Workout session notifier ===

final workoutSessionProvider =
    NotifierProvider<WorkoutSessionNotifier, WorkoutSessionState>(
        WorkoutSessionNotifier.new);

class WorkoutSessionState {
  const WorkoutSessionState({
    this.workoutName,
    this.dayNumber,
    this.planId,
    this.sets = const [],
    this.startedAt,
    this.completedAt,
  });

  final String? workoutName;
  final int? dayNumber;
  final String? planId;
  final List<SetEntry> sets;
  final DateTime? startedAt;
  final DateTime? completedAt;

  bool get isActive => workoutName != null && completedAt == null;

  WorkoutSessionState copyWith({
    String? workoutName,
    int? dayNumber,
    String? planId,
    List<SetEntry>? sets,
    DateTime? startedAt,
    DateTime? completedAt,
  }) {
    return WorkoutSessionState(
      workoutName: workoutName ?? this.workoutName,
      dayNumber: dayNumber ?? this.dayNumber,
      planId: planId ?? this.planId,
      sets: sets ?? this.sets,
      startedAt: startedAt ?? this.startedAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }
}

class WorkoutSessionNotifier extends Notifier<WorkoutSessionState> {
  @override
  WorkoutSessionState build() => const WorkoutSessionState();

  void start({
    required String workoutName,
    required int dayNumber,
    required String planId,
    required List<SetEntry> initialSets,
  }) {
    state = WorkoutSessionState(
      workoutName: workoutName,
      dayNumber: dayNumber,
      planId: planId,
      sets: initialSets,
      startedAt: DateTime.now(),
    );
  }

  void toggleSet(int index) {
    final sets = List<SetEntry>.from(state.sets);
    if (index >= sets.length) return;
    final s = sets[index];
    sets[index] = SetEntry(
      exerciseSlug: s.exerciseSlug,
      setNum: s.setNum,
      weightKg: s.weightKg,
      reps: s.reps,
      rpe: s.rpe,
      done: !s.done,
      completedAt: !s.done ? DateTime.now() : s.completedAt,
    );
    state = state.copyWith(sets: sets);
  }

  void updateSet(int index, {double? weightKg, int? reps, double? rpe}) {
    final sets = List<SetEntry>.from(state.sets);
    if (index >= sets.length) return;
    final s = sets[index];
    sets[index] = SetEntry(
      exerciseSlug: s.exerciseSlug,
      setNum: s.setNum,
      weightKg: weightKg ?? s.weightKg,
      reps: reps ?? s.reps,
      rpe: rpe ?? s.rpe,
      done: s.done,
      completedAt: s.completedAt,
    );
    state = state.copyWith(sets: sets);
  }

  void addSet(String exerciseSlug) {
    final sets = List<SetEntry>.from(state.sets);
    final lastSetNum = sets
        .where((s) => s.exerciseSlug == exerciseSlug)
        .fold(0, (m, s) => s.setNum > m ? s.setNum : m);
    sets.add(SetEntry(
      exerciseSlug: exerciseSlug,
      setNum: lastSetNum + 1,
      done: false,
      completedAt: DateTime.now(),
    ));
    state = state.copyWith(sets: sets);
  }

  Future<void> finish() async {
    if (state.workoutName == null || state.planId == null) return;
    final repo = ref.read(workoutLogRepoProvider);
    final record = WorkoutLogRecord(
      userId: ref.read(appNotifierProvider).value?.auth?.userId ?? 'anonymous',
      planId: state.planId!,
      dayNumber: state.dayNumber ?? 1,
      startedAt: state.startedAt ?? DateTime.now(),
      completedAt: DateTime.now(),
      workoutName: state.workoutName!,
      dataJson: '[]',
      syncStatus: 'pending',
    )
      ..sets = state.sets;
    await repo.put(record);
    state = const WorkoutSessionState();
  }

  void cancel() {
    state = const WorkoutSessionState();
  }
}

// === Progress notifier (weight + intake logging) ===

final progressProvider =
    NotifierProvider<ProgressNotifier, ProgressState>(ProgressNotifier.new);

class ProgressState {
  const ProgressState({
    this.weightLogs = const [],
    this.intakeLogs = const [],
    this.workoutLogs = const [],
  });

  final List<WeightLogRecord> weightLogs;
  final List<IntakeLogRecord> intakeLogs;
  final List<WorkoutLogRecord> workoutLogs;

  ProgressState copyWith({
    List<WeightLogRecord>? weightLogs,
    List<IntakeLogRecord>? intakeLogs,
    List<WorkoutLogRecord>? workoutLogs,
  }) {
    return ProgressState(
      weightLogs: weightLogs ?? this.weightLogs,
      intakeLogs: intakeLogs ?? this.intakeLogs,
      workoutLogs: workoutLogs ?? this.workoutLogs,
    );
  }
}

class ProgressNotifier extends Notifier<ProgressState> {
  @override
  ProgressState build() {
    _load();
    return const ProgressState();
  }

  Future<void> _load() async {
    final weightRepo = ref.read(weightLogRepoProvider);
    final intakeRepo = ref.read(intakeLogRepoProvider);
    final workoutRepo = ref.read(workoutLogRepoProvider);
    final weights = await weightRepo.all();
    final intakes = await intakeRepo.all();
    final workouts = await workoutRepo.all();
    weights.sort((a, b) => a.date.compareTo(b.date));
    intakes.sort((a, b) => a.date.compareTo(b.date));
    workouts.sort((a, b) => b.startedAt.compareTo(a.startedAt));
    state = ProgressState(
      weightLogs: weights,
      intakeLogs: intakes,
      workoutLogs: workouts,
    );
  }

  Future<void> logWeight(double weightKg, {DateTime? date}) async {
    final repo = ref.read(weightLogRepoProvider);
    final record = WeightLogRecord(
      userId: ref.read(appNotifierProvider).value?.auth?.userId ?? 'anonymous',
      date: date ?? DateTime.now(),
      weightKg: weightKg,
      syncStatus: 'pending',
    );
    await repo.put(record);
    await _load();
  }

  Future<void> logIntake(double intakeKcal, {DateTime? date}) async {
    final repo = ref.read(intakeLogRepoProvider);
    final record = IntakeLogRecord(
      userId: ref.read(appNotifierProvider).value?.auth?.userId ?? 'anonymous',
      date: date ?? DateTime.now(),
      intakeKcal: intakeKcal,
      syncStatus: 'pending',
    );
    await repo.put(record);
    await _load();
  }

  Future<void> reload() async => await _load();
}

// === Auth notifier ===

final authNotifierProvider =
    NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    _init();
    return const AuthState();
  }

  Future<void> _init() async {
    final client = Supabase.instance.client;
    final sub = client.auth.onAuthStateChange.listen((event) {
      state = AuthState(
        session: event.session,
        status: event.session != null
            ? AuthStatus.authenticated
            : AuthStatus.anonymous,
        email: event.session?.user.email,
      );
      // Sync auth state to AppNotifier.
      Future.microtask(() {
        ref.read(appNotifierProvider.notifier).setAuth(state);
      });
    });
    ref.onDispose(sub.cancel);
  }

  Future<void> signInWithMagicLink(String email) async {
    final client = Supabase.instance.client;
    await client.auth.signInWithOtp(email: email);
  }

  Future<void> signInWithOAuth(String provider) async {
    final client = Supabase.instance.client;
    await client.auth.signInWithOAuth(
      OAuthProvider.parse(provider),
      redirectTo: 'com.fitn.app://auth/callback',
    );
  }

  Future<void> signOut() async {
    final client = Supabase.instance.client;
    await client.auth.signOut();
    await ref.read(appNotifierProvider.notifier).clearOnSignOut();
  }
}

// === JSON encode helper ===
// dart:convert's jsonEncode is re-exported via the import above.
