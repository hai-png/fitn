/// Progress tab — weight/intake logs + workout history. See spec §7.7.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../theme/app_theme.dart';

class ProgressTab extends ConsumerWidget {
  const ProgressTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final progress = ref.watch(progressProvider);
    final appState = ref.watch(appNotifierProvider).valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Progress'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _WeightSection(
              logs: progress.weightLogs,
              currentWeight: appState?.profile?.weightKg ?? 0,
            ),
            const SizedBox(height: 16),
            _IntakeSection(
              logs: progress.intakeLogs,
              targetKcal: appState?.activePlan?.nutrition.calories.targetCaloriesKcal ?? 2500,
            ),
            const SizedBox(height: 16),
            _WorkoutHistorySection(logs: progress.workoutLogs),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }
}

class _WeightSection extends ConsumerWidget {
  const _WeightSection({required this.logs, required this.currentWeight});
  final List<WeightLogRecord> logs;
  final double currentWeight;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recent = logs.length > 90 ? logs.sublist(logs.length - 90) : logs;
    final current = logs.isNotEmpty ? logs.last.weightKg : currentWeight;
    final start = logs.isNotEmpty ? logs.first.weightKg : currentWeight;
    final delta = current - start;
    final avg7 = logs.length >= 7
        ? logs.sublist(logs.length - 7).map((e) => e.weightKg).reduce((a, b) => a + b) /
            7
        : current;
    final avg30 = logs.length >= 30
        ? logs
                .sublist(logs.length - 30)
                .map((e) => e.weightKg)
                .reduce((a, b) => a + b) /
            30
        : current;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(LucideIcons.scale, color: AppColors.primary),
                const SizedBox(width: 8),
                const Text('Weight Log',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const Spacer(),
                IconButton(
                  icon: const Icon(LucideIcons.plus),
                  onPressed: () => _showWeightDialog(context, ref),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (recent.length >= 2)
              SizedBox(
                height: 120,
                child: LineChart(
                  LineChartData(
                    gridData: const FlGridData(show: false),
                    titlesData: const FlTitlesData(show: false),
                    borderData: FlBorderData(show: false),
                    lineBarsData: [
                      LineChartBarData(
                        spots: recent
                            .asMap()
                            .entries
                            .map((e) =>
                                FlSpot(e.key.toDouble(), e.value.weightKg))
                            .toList(),
                        isCurved: true,
                        color: AppColors.primary,
                        barWidth: 3,
                        dotData: const FlDotData(show: false),
                        belowBarData: BarAreaData(
                          color: AppColors.primary.withValues(alpha: 0.15),
                          show: true,
                        ),
                      ),
                    ],
                  ),
                ),
              )
            else
              const SizedBox(
                height: 120,
                child: Center(
                  child: Text('Log your weight to see the chart',
                      style: TextStyle(color: AppColors.textSecondaryDark)),
                ),
              ),
            const SizedBox(height: 12),
            Row(
              children: [
                _StatCell('Current', '${current.toStringAsFixed(1)} kg'),
                _StatCell('7-day avg', avg7.toStringAsFixed(1)),
                _StatCell('30-day avg', avg30.toStringAsFixed(1)),
                _StatCell(
                    'Δ', '${delta >= 0 ? '+' : ''}${delta.toStringAsFixed(1)}'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showWeightDialog(BuildContext context, WidgetRef ref) async {
    final ctrl = TextEditingController();
    final picked = await showDialog<double>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Log Weight'),
          content: TextField(
            controller: ctrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
                labelText: 'Weight (kg)', suffixText: 'kg'),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () {
                final v = double.tryParse(ctrl.text);
                Navigator.pop(context, v);
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
    if (picked != null && picked >= 30 && picked <= 300) {
      await ref.read(progressProvider.notifier).logWeight(picked);
    }
  }
}

class _IntakeSection extends ConsumerWidget {
  const _IntakeSection({required this.logs, required this.targetKcal});
  final List<IntakeLogRecord> logs;
  final double targetKcal;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recent = logs.length > 30 ? logs.sublist(logs.length - 30) : logs;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(LucideIcons.flame, color: AppColors.accent),
                const SizedBox(width: 8),
                const Text('Intake Log',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const Spacer(),
                IconButton(
                  icon: const Icon(LucideIcons.plus),
                  onPressed: () => _showIntakeDialog(context, ref),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (recent.length >= 2)
              SizedBox(
                height: 100,
                child: LineChart(
                  LineChartData(
                    gridData: const FlGridData(show: false),
                    titlesData: const FlTitlesData(show: false),
                    borderData: FlBorderData(show: false),
                    minY: 0,
                    maxY: targetKcal * 1.5,
                    extraLinesData: ExtraLinesData(
                      horizontalLines: [
                        HorizontalLine(
                          y: targetKcal,
                          color: AppColors.primary.withValues(alpha: 0.4),
                          strokeWidth: 1,
                          dashArray: [4, 4],
                        ),
                      ],
                    ),
                    lineBarsData: [
                      LineChartBarData(
                        spots: recent
                            .asMap()
                            .entries
                            .map((e) =>
                                FlSpot(e.key.toDouble(), e.value.intakeKcal))
                            .toList(),
                        isCurved: true,
                        color: AppColors.accent,
                        barWidth: 3,
                        dotData: const FlDotData(show: false),
                      ),
                    ],
                  ),
                ),
              )
            else
              const SizedBox(
                height: 100,
                child: Center(
                  child: Text('Log your daily intake to see the chart',
                      style: TextStyle(color: AppColors.textSecondaryDark)),
                ),
              ),
            const SizedBox(height: 8),
            Text('Target: ${targetKcal.round()} kcal/day',
                style: const TextStyle(
                    color: AppColors.textSecondaryDark, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Future<void> _showIntakeDialog(BuildContext context, WidgetRef ref) async {
    final ctrl = TextEditingController();
    final picked = await showDialog<double>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Log Intake'),
          content: TextField(
            controller: ctrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
                labelText: 'Intake (kcal)', suffixText: 'kcal'),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () {
                final v = double.tryParse(ctrl.text);
                Navigator.pop(context, v);
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
    if (picked != null && picked >= 0 && picked <= 10000) {
      await ref.read(progressProvider.notifier).logIntake(picked);
    }
  }
}

class _WorkoutHistorySection extends StatelessWidget {
  const _WorkoutHistorySection({required this.logs});
  final List<WorkoutLogRecord> logs;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(LucideIcons.history, color: AppColors.info),
                const SizedBox(width: 8),
                const Text('Workout History',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ],
            ),
            const SizedBox(height: 12),
            if (logs.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: Center(
                  child: Text('No workouts logged yet',
                      style: TextStyle(color: AppColors.textSecondaryDark)),
                ),
              )
            else
              ...logs.take(20).map((log) {
                final duration = log.completedAt != null
                    ? log.completedAt!.difference(log.startedAt).inMinutes
                    : 0;
                final sets = log.sets.where((s) => s.done).length;
                final volume = log.sets
                    .where((s) => s.done && s.weightKg != null && s.reps != null)
                    .fold(0.0, (a, s) => a + s.weightKg! * s.reps!);
                return ListTile(
                  dense: true,
                  leading: CircleAvatar(
                    backgroundColor: AppColors.info.withValues(alpha: 0.15),
                    child: const Icon(LucideIcons.dumbbell,
                        color: AppColors.info, size: 18),
                  ),
                  title: Text(log.workoutName,
                      style:
                          const TextStyle(fontWeight: FontWeight.w500)),
                  subtitle: Text(
                    '${log.startedAt.ymd} · $duration min · $sets sets · ${volume.round()} kg volume',
                    style: const TextStyle(
                        color: AppColors.textSecondaryDark, fontSize: 11),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }
}

class _StatCell extends StatelessWidget {
  const _StatCell(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(value,
              style: const TextStyle(
                  fontSize: 14, fontWeight: FontWeight.w600)),
          Text(label,
              style: const TextStyle(
                  color: AppColors.textSecondaryDark, fontSize: 10)),
        ],
      ),
    );
  }
}
