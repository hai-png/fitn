/// Progress tab — weight + water + workout logs + advanced analytics.
/// Matches FitLife Hub design.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../data/domain_types.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class ProgressTab extends ConsumerStatefulWidget {
  const ProgressTab({super.key});

  @override
  ConsumerState<ProgressTab> createState() => _ProgressTabState();
}

class _ProgressTabState extends ConsumerState<ProgressTab> {
  String _subTab = 'metrics'; // metrics | muscles | exercises | visuals

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final weightLogs = appState?.weightLogs ?? const [];
    final waterLogs = appState?.waterLogs ?? const [];
    final workoutLogs = appState?.workoutLogs ?? const [];
    final exerciseLogs = appState?.exerciseLogs ?? const [];
    final targetKcal = appState?.activePlan?.nutrition.calories.targetCaloriesKcal ?? 2000;
    final waterTargetMl = 3000;

    final currentWeight = weightLogs.isNotEmpty ? weightLogs.last.weightKg : (appState?.profile?.weightKg ?? 75);
    final initialWeight = weightLogs.isNotEmpty ? weightLogs.first.weightKg : (appState?.profile?.weightKg ?? 75);
    final weightDiff = currentWeight - initialWeight;
    final today = DateTime.now();
    final todayWater = waterLogs
        .where((w) => _sameDay(w.date, today))
        .fold(0, (s, w) => s + w.amountMl);
    final waterPct = (todayWater / waterTargetMl * 100).clamp(0, 100).round();

    // Lifetime volume calculation.
    final lifetimeVolumeKg = exerciseLogs.fold<double>(0, (exSum, ex) {
      return exSum + ex.sets.fold<double>(0, (s, set) => s + (set.isWarmUp ? 0 : set.weight * set.reps));
    });
    final lifetimeTons = (lifetimeVolumeKg / 1000 * 10).round() / 10;
    final tier = _tierFor(lifetimeTons);

    return Scaffold(
      backgroundColor: FitnColors.cream,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
          children: [
            // Title.
            FitnSectionLabel('03 — Training Metrics & History'),
            Text('Performance Logs', style: FitnText.headline.copyWith(fontSize: 28)),
            const SizedBox(height: 20),
            // Weight log card.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(LucideIcons.scale, size: 14, color: FitnColors.accent),
                      const SizedBox(width: 6),
                      Text('WEIGHT LOG', style: FitnText.microLabel),
                      const Spacer(),
                      IconButton(
                        icon: Icon(LucideIcons.plus, size: 16, color: FitnColors.ink),
                        onPressed: () => _showWeightDialog(context, ref),
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (weightLogs.length >= 2)
                    SizedBox(
                      height: 120,
                      child: LineChart(
                        LineChartData(
                          gridData: const FlGridData(show: false),
                          titlesData: const FlTitlesData(show: false),
                          borderData: FlBorderData(show: false),
                          lineBarsData: [
                            LineChartBarData(
                              spots: weightLogs
                                  .asMap()
                                  .entries
                                  .map((e) => FlSpot(e.key.toDouble(), e.value.weightKg))
                                  .toList(),
                              isCurved: true,
                              color: FitnColors.accent,
                              barWidth: 2,
                              dotData: const FlDotData(show: false),
                              belowBarData: BarAreaData(
                                color: FitnColors.accent10,
                                show: true,
                              ),
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    SizedBox(
                      height: 120,
                      child: Center(
                        child: Text('Log your weight to see the chart',
                            style: FitnText.serifItalic),
                      ),
                    ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _statCell(
                            'CURRENT', '${currentWeight.toStringAsFixed(1)} kg'),
                      ),
                      Expanded(
                        child: _statCell(
                            'INITIAL', '${initialWeight.toStringAsFixed(1)} kg'),
                      ),
                      Expanded(
                        child: _statCell(
                            'Δ',
                            '${weightDiff >= 0 ? '+' : ''}${weightDiff.toStringAsFixed(1)} kg',
                            accent: weightDiff < 0),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            // Water log card.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(LucideIcons.droplet, size: 14, color: FitnColors.accent),
                      const SizedBox(width: 6),
                      Text('HYDRATION TODAY', style: FitnText.microLabel),
                      const Spacer(),
                      Text('$todayWater / $waterTargetMl ml',
                          style: FitnText.mono.copyWith(
                              fontSize: 11, color: FitnColors.accent)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ClipRRect(
                    child: LinearProgressIndicator(
                      value: waterPct / 100,
                      minHeight: 12,
                      color: FitnColors.accent,
                      backgroundColor: FitnColors.fill,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () => ref
                              .read(appNotifierProvider.notifier)
                              .logWater(250),
                          icon: Icon(LucideIcons.plus, size: 14),
                          label: Text('+250 ML',
                              style: GoogleFonts.inter(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.0)),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () => ref
                              .read(appNotifierProvider.notifier)
                              .logWater(500),
                          icon: Icon(LucideIcons.plus, size: 14),
                          label: Text('+500 ML',
                              style: GoogleFonts.inter(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.0)),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            // Workout history card.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(LucideIcons.history, size: 14, color: FitnColors.accent),
                      const SizedBox(width: 6),
                      Text('WORKOUT HISTORY', style: FitnText.microLabel),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (workoutLogs.isEmpty)
                    Padding(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      child: Center(
                        child: Text('No workouts logged yet',
                            style: FitnText.serifItalic),
                      ),
                    )
                  else
                    ...workoutLogs.take(8).map((log) {
                      final duration = log.completedAt != null
                          ? log.completedAt!.difference(log.startedAt).inMinutes
                          : 0;
                      final sets = log.sets.where((s) => s.done).length;
                      return ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        leading: Container(
                          width: 32,
                          height: 32,
                          color: FitnColors.accent05,
                          child: Icon(LucideIcons.dumbbell,
                              size: 16, color: FitnColors.accent),
                        ),
                        title: Text(log.workoutName,
                            style: GoogleFonts.inter(
                                fontSize: 12, fontWeight: FontWeight.w700)),
                        subtitle: Text(
                          '${log.startedAt.year}-${log.startedAt.month.toString().padLeft(2, '0')}-${log.startedAt.day.toString().padLeft(2, '0')} • $duration min • $sets sets',
                          style: FitnText.monoSmall.copyWith(fontSize: 10),
                        ),
                      );
                    }),
                ],
              ),
            ),
            const SizedBox(height: 12),
            // Lifetime volume tier card.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                  Row(
                    children: [
                      Icon(LucideIcons.award, size: 14, color: FitnColors.accent),
                      const SizedBox(width: 6),
                      Text('LIFETIME VOLUME TIER', style: FitnText.microLabel),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text('$lifetimeTons t',
                      style: FitnText.headline.copyWith(fontSize: 32)),
                  const SizedBox(height: 4),
                  Text('Current tier: ${tier.name}',
                      style: FitnText.serifItalic.copyWith(fontSize: 11)),
                ],
              ),
            ),
            const SizedBox(height: 12),
            // Target vs intake card.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(LucideIcons.flame, size: 14, color: FitnColors.accent),
                      const SizedBox(width: 6),
                      Text('DAILY TARGET', style: FitnText.microLabel),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('$targetKcal kcal',
                      style: FitnText.headline.copyWith(fontSize: 24)),
                  const SizedBox(height: 4),
                  Text('Suggested daily intake',
                      style: FitnText.serifItalic.copyWith(fontSize: 10)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _statCell(String label, String value, {bool accent = false}) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: FitnColors.fill,
        border: Border.all(color: FitnColors.ink05, width: 1),
      ),
      child: Column(
        children: [
          Text(label,
              style: GoogleFonts.inter(
                  fontSize: 8,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                  color: FitnColors.ink40)),
          const SizedBox(height: 4),
          Text(
            value,
            style: FitnText.mono.copyWith(
                fontSize: 11,
                color: accent ? FitnColors.accent : FitnColors.ink,
                fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  LifetimeTier _tierFor(double tons) {
    for (final t in lifetimeTiers) {
      if (tons >= t.minTons && tons < t.maxTons) return t;
    }
    return lifetimeTiers.last;
  }

  Future<void> _showWeightDialog(BuildContext context, WidgetRef ref) async {
    final ctrl = TextEditingController();
    final picked = await showDialog<double>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Log Weight', style: FitnText.headline.copyWith(fontSize: 18)),
        content: TextField(
          controller: ctrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Weight (kg)'),
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
      ),
    );
    if (picked != null && picked >= 30 && picked <= 300) {
      await ref.read(appNotifierProvider.notifier).logWeight(picked);
    }
  }
}
