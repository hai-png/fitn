/// Home tab — dashboard. See spec §7.3.
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appAsync = ref.watch(appNotifierProvider);
    final appState = appAsync.valueOrNull;

    if (!appState!.hasOnboarded || appState.activePlan == null) {
      return const Center(child: Text('No plan yet. Complete onboarding.'));
    }

    final plan = appState.activePlan!;
    final profile = appState.profile!;
    final assessment = plan; // we'd need GeneratePlanResponse for full data

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (appState.planStale) _buildStalenessBanner(ref),
            _buildGreeting(context, profile),
            const SizedBox(height: 16),
            _buildTodayWorkoutCard(context, plan, ref),
            const SizedBox(height: 16),
            _buildDailyTargetCard(context, plan),
            const SizedBox(height: 16),
            _buildStatGrid(plan),
            const SizedBox(height: 16),
            _buildBodyCompCard(plan, profile),
            const SizedBox(height: 16),
            _buildThreePillars(context, ref),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildStalenessBanner(WidgetRef ref) {
    return Card(
      color: AppColors.warning.withValues(alpha: 0.15),
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: AppColors.warning)),
      child: ListTile(
        leading: const Icon(LucideIcons.alertTriangle, color: AppColors.warning),
        title: const Text('Your plan is out of date'),
        trailing: TextButton(
          onPressed: () {
            ref.read(appNotifierProvider.notifier).setActiveTab(Tab.profile);
          },
          child: const Text('Update'),
        ),
      ),
    ).animate().slideY(begin: -0.2, duration: 300.ms);
  }

  Widget _buildGreeting(BuildContext context, UserProfile profile) {
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good morning'
        : hour < 18
            ? 'Good afternoon'
            : 'Good evening';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('$greeting 👋',
            style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 4),
        Text(
          '${profile.primaryGoal.display} · ${profile.trainingStatus.display}',
          style: const TextStyle(color: AppColors.textSecondaryDark),
        ),
      ],
    );
  }

  Widget _buildTodayWorkoutCard(
      BuildContext context, FitnessPlan plan, WidgetRef ref) {
    final today = DateTime.now().weekday;
    final training = plan.training;
    final workout = training.mesocycles.isNotEmpty &&
            training.mesocycles.first.microcycles.isNotEmpty
        ? training.mesocycles.first.microcycles.first.workouts.firstOrNull
        : null;
    final isToday = workout != null && workout.dayNumber == today;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(LucideIcons.dumbbell,
                  color: AppColors.primary, size: 28),
            )
                .animate(onPlay: (c) => c.repeat())
                .shimmer(duration: 2.seconds, color: AppColors.primary),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isToday ? "Today's Workout" : 'Next Workout',
                    style: const TextStyle(
                        color: AppColors.textSecondaryDark, fontSize: 12),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    workout?.name ?? 'Rest day',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    workout != null
                        ? '${workout.exercises.length} exercises · ${workout.estimatedDurationMin} min'
                        : 'Recover and recharge',
                    style: const TextStyle(
                        color: AppColors.textSecondaryDark, fontSize: 12),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(LucideIcons.chevronRight),
              onPressed: () {
                ref.read(appNotifierProvider.notifier).setActiveTab(Tab.workouts);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDailyTargetCard(BuildContext context, FitnessPlan plan) {
    final kcal = plan.nutrition.calories.targetCaloriesKcal;
    final tdee = plan.nutrition.tdee.finalTdeeKcal;
    final delta = kcal - tdee;
    final macros = plan.nutrition.macros;
    final ffmiPct = 0.7; // placeholder

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Daily Target',
                style: TextStyle(
                    color: AppColors.textSecondaryDark, fontSize: 12)),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                AnimatedNumber(
                  value: kcal,
                  style: const TextStyle(
                      fontSize: 40, fontWeight: FontWeight.w700),
                ),
                const Text(' kcal',
                    style: TextStyle(color: AppColors.textSecondaryDark)),
                const Spacer(),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: delta < 0
                        ? AppColors.danger.withValues(alpha: 0.15)
                        : AppColors.success.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '${delta > 0 ? '+' : ''}${delta.round()} kcal',
                    style: TextStyle(
                      color: delta < 0 ? AppColors.danger : AppColors.success,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                MacroRing(
                  label: 'Protein',
                  current: 0,
                  target: macros.proteinG,
                  unit: 'g',
                  color: AppColors.proteinRing,
                ),
                MacroRing(
                  label: 'Carbs',
                  current: 0,
                  target: macros.carbG,
                  unit: 'g',
                  color: AppColors.carbRing,
                ),
                MacroRing(
                  label: 'Fat',
                  current: 0,
                  target: macros.fatG,
                  unit: 'g',
                  color: AppColors.fatRing,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                ProgressRing(
                  progress: ffmiPct,
                  size: 48,
                  strokeWidth: 5,
                  child: Text('${(ffmiPct * 100).round()}%',
                      style: const TextStyle(fontSize: 11)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(plan.nutrition.calories.rateLabel,
                          style: const TextStyle(
                              fontWeight: FontWeight.w600, fontSize: 13)),
                      const Text('FFMI % of natural ceiling',
                          style: TextStyle(
                              color: AppColors.textSecondaryDark,
                              fontSize: 11)),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatGrid(FitnessPlan plan) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 2.2,
      children: [
        _StatCard(
          icon: LucideIcons.droplets,
          label: 'Hydration',
          value:
              '${plan.nutrition.hydration.waterLitersPerDay.toStringAsFixed(1)} L',
          color: AppColors.info,
        ),
        _StatCard(
          icon: LucideIcons.wheat,
          label: 'Fiber',
          value: '${plan.nutrition.micronutrients.fiberG.round()} g',
          color: AppColors.fiberRing,
        ),
        _StatCard(
          icon: LucideIcons.calendar,
          label: 'Timeline',
          value: '${plan.nutrition.timelineWeeks} weeks',
          color: AppColors.accent,
        ),
        _StatCard(
          icon: LucideIcons.activity,
          label: 'FFMI',
          value: '—',
          color: AppColors.primary,
        ),
      ],
    );
  }

  Widget _buildBodyCompCard(FitnessPlan plan, UserProfile profile) {
    // Without assessment data, we show profile-derived metrics.
    final bmi = profile.bmi;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Body Composition',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _MetricBar(
                    label: 'BMI',
                    value: bmi.toStringAsFixed(1),
                    progress: (bmi / 35).clamp(0.0, 1.0),
                    color: AppColors.info,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _MetricBar(
                    label: 'BF %',
                    value: profile.bodyFatPct?.toStringAsFixed(1) ?? '—',
                    progress: ((profile.bodyFatPct ?? 0) / 40).clamp(0.0, 1.0),
                    color: AppColors.accent,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildThreePillars(BuildContext context, WidgetRef ref) {
    return Row(
      children: [
        Expanded(
          child: _PillarCard(
            icon: LucideIcons.dumbbell,
            label: 'Workouts',
            color: AppColors.primary,
            onTap: () =>
                ref.read(appNotifierProvider.notifier).setActiveTab(Tab.workouts),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _PillarCard(
            icon: LucideIcons.utensils,
            label: 'Meals',
            color: AppColors.accent,
            onTap: () =>
                ref.read(appNotifierProvider.notifier).setActiveTab(Tab.meals),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _PillarCard(
            icon: LucideIcons.trendingUp,
            label: 'Progress',
            color: AppColors.info,
            onTap: () => ref
                .read(appNotifierProvider.notifier)
                .setActiveTab(Tab.progress),
          ),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 18),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(value,
                      style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w600)),
                  Text(label,
                      style: const TextStyle(
                          color: AppColors.textSecondaryDark, fontSize: 11)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetricBar extends StatelessWidget {
  const _MetricBar({
    required this.label,
    required this.value,
    required this.progress,
    required this.color,
  });
  final String label;
  final String value;
  final double progress;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: const TextStyle(
                    color: AppColors.textSecondaryDark, fontSize: 12)),
            Text(value,
                style: const TextStyle(
                    fontWeight: FontWeight.w600, fontSize: 14)),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progress.clamp(0.0, 1.0),
            minHeight: 6,
            color: color,
            backgroundColor: color.withValues(alpha: 0.15),
          ),
        ),
      ],
    );
  }
}

class _PillarCard extends StatelessWidget {
  const _PillarCard({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Column(
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(height: 8),
              Text(label,
                  style: const TextStyle(
                      fontSize: 12, fontWeight: FontWeight.w500)),
            ],
          ),
        ),
      ),
    );
  }
}
