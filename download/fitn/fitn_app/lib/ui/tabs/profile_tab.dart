/// Profile tab. See spec §7.8.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../theme/app_theme.dart';

class ProfileTab extends ConsumerWidget {
  const ProfileTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appAsync = ref.watch(appNotifierProvider);
    final appState = appAsync.valueOrNull;
    final profile = appState?.profile;
    final plan = appState?.activePlan;
    final auth = appState?.auth;

    if (profile == null) {
      return const Center(child: Text('No profile yet.'));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.settings),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const _SettingsLink()),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildHeader(profile),
            const SizedBox(height: 16),
            if (plan != null) _buildStrategyCard(plan, profile),
            const SizedBox(height: 16),
            _buildProfileDetailsCard(profile),
            const SizedBox(height: 16),
            _buildPlanHistoryCard(appState?.planHistory ?? [], ref),
            const SizedBox(height: 16),
            _buildQuickActions(ref),
            const SizedBox(height: 16),
            _buildAuthSection(auth, ref),
            const SizedBox(height: 32),
            const Center(
              child: Text(
                'Engine v3.2.0 · Deterministic\nAll data stays on your device',
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: AppColors.textSecondaryDark, fontSize: 11),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(UserProfile p) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 32,
              backgroundColor: AppColors.primary,
              child: Text(
                p.sex == Sex.male ? 'M' : 'F',
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w700),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${p.sex.display} · ${p.age}y',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${p.heightCm.toStringAsFixed(0)}cm · ${p.weightKg.toStringAsFixed(1)}kg',
                    style: const TextStyle(
                        color: AppColors.textSecondaryDark),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(LucideIcons.edit),
              onPressed: () {
                // Edit bottom sheet.
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStrategyCard(FitnessPlan plan, UserProfile p) {
    final strategy = plan.nutrition.calories.strategy;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(LucideIcons.target, color: AppColors.primary),
                const SizedBox(width: 8),
                const Text('Recommended Strategy',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ],
            ),
            const SizedBox(height: 12),
            Text(strategy.display,
                style: const TextStyle(
                    fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.primary)),
            const SizedBox(height: 8),
            Text(
                'Target ${plan.nutrition.calories.targetCaloriesKcal.round()} kcal/day (${plan.nutrition.calories.rateLabel})',
                style: const TextStyle(color: AppColors.textSecondaryDark)),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileDetailsCard(UserProfile p) {
    final rows = <(String, String)>[
      ('Activity', p.activityLevel.display),
      ('Status', p.trainingStatus.display),
      ('Goal', p.primaryGoal.display),
      ('Equipment', p.equipmentAccess.display),
      ('Diet', p.dietType.display),
      ('Training days', '${p.trainingDaysPerWeek}/week'),
      ('Time of day', p.trainingTimeOfDay.display),
      if (p.bodyFatPct != null)
        ('Body fat', '${p.bodyFatPct!.toStringAsFixed(1)}%'),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Profile Details',
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            ...rows.map((r) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    children: [
                      SizedBox(
                          width: 100,
                          child: Text(r.$1,
                              style: const TextStyle(
                                  color: AppColors.textSecondaryDark,
                                  fontSize: 12))),
                      Expanded(
                          child: Text(r.$2,
                              style: const TextStyle(fontSize: 13))),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildPlanHistoryCard(List<PlanRecord> history, WidgetRef ref) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Plan History',
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            if (history.isEmpty)
              const Text('No plans yet',
                  style: TextStyle(color: AppColors.textSecondaryDark))
            else
              ...history.take(5).map((p) => ListTile(
                    dense: true,
                    leading: Icon(
                        p.isActive ? LucideIcons.check : LucideIcons.history,
                        color: p.isActive
                            ? AppColors.primary
                            : AppColors.textSecondaryDark,
                        size: 18),
                    title: Text(
                        '${p.generatedAt.ymd} · v${p.engineVersion}',
                        style: const TextStyle(fontSize: 13)),
                    trailing: p.isActive
                        ? const Text('Active',
                            style: TextStyle(
                                color: AppColors.primary, fontSize: 11))
                        : TextButton(
                            onPressed: () => ref
                                .read(appNotifierProvider.notifier)
                                .restorePlan(p.planId),
                            child: const Text('Restore'),
                          ),
                  )),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActions(WidgetRef ref) {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () => ref.read(appNotifierProvider.notifier).generatePlan(),
            icon: const Icon(LucideIcons.refreshCw),
            label: const Text('Regenerate Plan'),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: () => ref
                .read(appNotifierProvider.notifier)
                .setActiveTab(Tab.home),
            icon: const Icon(LucideIcons.home),
            label: const Text('Dashboard'),
          ),
        ),
      ],
    );
  }

  Widget _buildAuthSection(AuthState? auth, WidgetRef ref) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Account',
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            if (auth?.isAuthenticated ?? false) ...[
              Text(auth!.email ?? 'Signed in',
                  style: const TextStyle(fontSize: 14)),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () =>
                    ref.read(authNotifierProvider.notifier).signOut(),
                icon: const Icon(LucideIcons.logOut),
                label: const Text('Sign out'),
              ),
              const SizedBox(height: 8),
              const Text(
                  'Note: signing out does NOT clear your local data. Your plan and logs persist on this device.',
                  style: TextStyle(
                      color: AppColors.textSecondaryDark, fontSize: 11)),
            ] else ...[
              const Text('Sign in to sync across devices',
                  style: TextStyle(
                      color: AppColors.textSecondaryDark, fontSize: 13)),
              const SizedBox(height: 8),
              ElevatedButton.icon(
                onPressed: () => Navigator.of(context).pushNamed('/signin'),
                icon: const Icon(LucideIcons.logIn),
                label: const Text('Sign in'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SettingsLink extends StatelessWidget {
  const _SettingsLink();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: const Center(child: Text('Settings — see settings_screen.dart')),
    );
  }
}
