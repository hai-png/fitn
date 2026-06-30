/// Progress tab — comprehensive analytics matching FitLife Hub design.
///
/// Sub-tabs:
/// - Metrics: core metrics + rolling trends + training focus splits
/// - Muscles: muscle volume zones + body map + balance analysis
/// - Exercises: PRs (Epley 1RM) + progression analysis
/// - Visuals: flex/share cards
///
/// Also includes: weight log, water log, workout history, lifetime volume tier.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../data/analytics_engine.dart';
import '../../data/domain_types.dart';
import '../../data/isar/collections/collections.dart';
import '../../engine/engine_provider.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class ProgressTab extends ConsumerStatefulWidget {
  const ProgressTab({super.key});

  @override
  ConsumerState<ProgressTab> createState() => _ProgressTabState();
}

class _ProgressTabState extends ConsumerState<ProgressTab> {
  String _subTab = 'metrics';
  String _selectedMuscle = 'Chest';
  String _selectedAnalysisEx = 'Flat Barbell Bench Press';
  bool _isSmoothedTrend = true;
  bool _isLogFormOpen = false;
  String? _activeShareCard;
  bool _copiedShareText = false;

  // Quick set logger form state.
  String _logExName = 'Flat Barbell Bench Press';
  String _logExMuscle = 'Chest';
  final _logExWeightCtrl = TextEditingController(text: '60');
  final _logExRepsCtrl = TextEditingController(text: '8');
  String _logExType = 'Normal';
  bool _logExIsWarmUp = false;

  @override
  void dispose() {
    _logExWeightCtrl.dispose();
    _logExRepsCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final weightLogs = appState?.weightLogs ?? const [];
    final waterLogs = appState?.waterLogs ?? const [];
    final workoutLogs = appState?.workoutLogs ?? const [];
    final exerciseLogs = appState?.exerciseLogs ?? const [];
    final targetKcal = appState?.activePlan?.nutrition.calories.targetCaloriesKcal ?? 2000;
    final waterTargetMl = 3000;

    // Seed exercise logs if empty (for demo).
    final effectiveLogs = exerciseLogs.isEmpty
        ? generateWorkoutHistory()
        : exerciseLogs;

    final currentWeight = weightLogs.isNotEmpty
        ? weightLogs.last.weightKg
        : (appState?.profile?.weightKg ?? 75);
    final initialWeight = weightLogs.isNotEmpty
        ? weightLogs.first.weightKg
        : (appState?.profile?.weightKg ?? 75);
    final weightDiff = currentWeight - initialWeight;
    final today = DateTime.now();
    final todayWater = waterLogs
        .where((w) => _sameDay(w.date, today))
        .fold(0, (s, w) => s + w.amountMl);
    final waterPct = (todayWater / waterTargetMl * 100).clamp(0, 100).round();

    // Lifetime volume.
    final lifetimeVolumeKg = effectiveLogs.fold<double>(0, (exSum, ex) {
      return exSum +
          ex.sets.fold<double>(
              0, (s, set) => s + (set.isWarmUp ? 0 : set.weight * set.reps));
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
            const SizedBox(height: 16),

            // === Sub-tab selector ===
            Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: FitnColors.ink05,
                border: Border.all(color: FitnColors.ink10, width: 1),
              ),
              child: Row(
                children: [
                  _subTabBtn('metrics', 'Metrics'),
                  _subTabBtn('muscles', 'Muscles'),
                  _subTabBtn('exercises', 'Exercises'),
                  _subTabBtn('visuals', 'Visuals'),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // === Sub-tab content ===
            if (_subTab == 'metrics')
              _buildMetricsSubTab(effectiveLogs, weightLogs, waterLogs,
                  workoutLogs, currentWeight, initialWeight, weightDiff,
                  todayWater, waterPct, waterTargetMl, lifetimeTons, tier,
                  targetKcal)
            else if (_subTab == 'muscles')
              _buildMusclesSubTab(effectiveLogs)
            else if (_subTab == 'exercises')
              _buildExercisesSubTab(effectiveLogs)
            else if (_subTab == 'visuals')
              _buildVisualsSubTab(effectiveLogs, lifetimeTons, tier,
                  currentWeight, weightDiff),
          ],
        ),
      ),
    );
  }

  // === Sub-tab button ===
  Widget _subTabBtn(String id, String label) {
    final selected = _subTab == id;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _subTab = id),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          color: selected ? FitnColors.ink : Colors.transparent,
          child: Text(label.toUpperCase(),
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: selected ? Colors.white : FitnColors.ink50)),
        ),
      ),
    );
  }

  // === METRICS sub-tab ===
  Widget _buildMetricsSubTab(
      List<ExerciseLog> logs,
      List<WeightLogRecord> weightLogs,
      List<WaterLog> waterLogs,
      List<WorkoutLogRecord> workoutLogs,
      double currentWeight,
      double initialWeight,
      double weightDiff,
      int todayWater,
      int waterPct,
      int waterTargetMl,
      double lifetimeTons,
      LifetimeTier tier,
      double targetKcal) {
    final coreMetrics = calculateCoreMetrics(logs);
    final rollingTrends = calculateRollingTrends(logs);

    // Training focus splits (strength/hypertrophy/endurance).
    int strengthSets = 0, hypertrophySets = 0, enduranceSets = 0, totalWorking = 0;
    for (final ex in logs) {
      for (final s in ex.sets) {
        if (s.isWarmUp) continue;
        totalWorking++;
        if (s.reps <= 5) {
          strengthSets++;
        } else if (s.reps <= 12) {
          hypertrophySets++;
        } else {
          enduranceSets++;
        }
      }
    }
    final strengthPct = totalWorking > 0 ? (strengthSets / totalWorking * 100).round() : 0;
    final hypertrophyPct = totalWorking > 0 ? (hypertrophySets / totalWorking * 100).round() : 0;
    final endurancePct = totalWorking > 0 ? (enduranceSets / totalWorking * 100).round() : 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
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
                    icon: Icon(LucideIcons.plus, size: 16),
                    onPressed: () => _showWeightDialog(),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (weightLogs.length >= 2)
                SizedBox(
                  height: 100,
                  child: LineChart(LineChartData(
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
                        belowBarData: BarAreaData(color: FitnColors.accent10, show: true),
                      ),
                    ],
                  )),
                )
              else
                SizedBox(
                  height: 100,
                  child: Center(
                    child: Text('Log your weight to see the chart',
                        style: FitnText.serifItalic),
                  ),
                ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _statCell('CURRENT', '${currentWeight.toStringAsFixed(1)} kg')),
                  Expanded(child: _statCell('INITIAL', '${initialWeight.toStringAsFixed(1)} kg')),
                  Expanded(child: _statCell('Δ',
                      '${weightDiff >= 0 ? '+' : ''}${weightDiff.toStringAsFixed(1)} kg',
                      accent: weightDiff < 0)),
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
                      style: FitnText.mono.copyWith(fontSize: 11, color: FitnColors.accent)),
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
                      onPressed: () => ref.read(appNotifierProvider.notifier).logWater(250),
                      icon: Icon(LucideIcons.plus, size: 14),
                      label: Text('+250 ML',
                          style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w700)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => ref.read(appNotifierProvider.notifier).logWater(500),
                      icon: Icon(LucideIcons.plus, size: 14),
                      label: Text('+500 ML',
                          style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w700)),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // Core metrics summary.
        Row(
          children: [
            Expanded(
              child: FitnCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('ACTIVE VOLUME', style: FitnText.microLabelAccent.copyWith(fontSize: 8)),
                    const SizedBox(height: 4),
                    Text('${coreMetrics.totalVolume.round()} kg',
                        style: FitnText.headline.copyWith(fontSize: 18)),
                    Text('${coreMetrics.totalWorkingSets} working sets',
                        style: FitnText.serifItalic.copyWith(fontSize: 9)),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: FitnCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('TEMPO & DENSITY', style: FitnText.microLabelAccent.copyWith(fontSize: 8)),
                    const SizedBox(height: 4),
                    Text('${coreMetrics.volumePerMinute.toStringAsFixed(1)} kg/min',
                        style: FitnText.headline.copyWith(fontSize: 18)),
                    Text('${coreMetrics.totalDuration} min total',
                        style: FitnText.serifItalic.copyWith(fontSize: 9)),
                  ],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Rolling trends.
        FitnCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(LucideIcons.activity, size: 14, color: FitnColors.accent),
                  const SizedBox(width: 6),
                  Text('ROLLING PERIODIC VELOCITY', style: FitnText.microLabel),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _rollingCell('7 DAYS', rollingTrends.vol7, rollingTrends.diff7)),
                  const SizedBox(width: 4),
                  Expanded(child: _rollingCell('30 DAYS', rollingTrends.vol30, rollingTrends.diff30)),
                  const SizedBox(width: 4),
                  Expanded(child: _rollingCell('1 YEAR', rollingTrends.vol365, rollingTrends.diff365)),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // Training focus splits.
        FitnCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('TRAINING FOCUS SPLITS', style: FitnText.microLabel),
              const SizedBox(height: 12),
              FitnMacroBar(
                label: 'Strength (1-5 reps)',
                value: '$strengthSets sets ($strengthPct%)',
                percentage: strengthPct.toDouble(),
                color: FitnColors.ink,
              ),
              const SizedBox(height: 8),
              FitnMacroBar(
                label: 'Hypertrophy (6-12 reps)',
                value: '$hypertrophySets sets ($hypertrophyPct%)',
                percentage: hypertrophyPct.toDouble(),
                color: FitnColors.accent,
              ),
              const SizedBox(height: 8),
              FitnMacroBar(
                label: 'Endurance (13+ reps)',
                value: '$enduranceSets sets ($endurancePct%)',
                percentage: endurancePct.toDouble(),
                color: FitnColors.ink40,
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // Lifetime volume tier.
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

        // Workout history.
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
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: Center(
                    child: Text('No workouts logged yet', style: FitnText.serifItalic),
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
      ],
    );
  }

  Widget _rollingCell(String label, double vol, double diff) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: FitnColors.fill,
        border: Border.all(color: FitnColors.ink05, width: 1),
      ),
      child: Column(
        children: [
          Text(label, style: FitnText.microLabel.copyWith(fontSize: 8)),
          const SizedBox(height: 4),
          Text('${(vol / 1000).toStringAsFixed(1)}t',
              style: FitnText.mono.copyWith(fontSize: 13, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(diff >= 0 ? LucideIcons.trendingUp : LucideIcons.trendingDown,
                  size: 10, color: diff >= 0 ? FitnColors.success : FitnColors.danger),
              const SizedBox(width: 2),
              Text('${diff >= 0 ? '+' : ''}${diff.toStringAsFixed(1)}%',
                  style: GoogleFonts.inter(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      color: diff >= 0 ? FitnColors.success : FitnColors.danger)),
            ],
          ),
        ],
      ),
    );
  }

  // === MUSCLES sub-tab ===
  Widget _buildMusclesSubTab(List<ExerciseLog> logs) {
    final zones = calculateMuscleVolumesAndScores(logs, 'Intermediate');
    final sorted = List<MuscleVolumeZone>.from(zones)
      ..sort((a, b) => b.balancePct.compareTo(a.balancePct));
    final top3Share = sorted.take(3).fold(0.0, (s, z) => s + z.balancePct);
    final isImbalanced = top3Share > 70;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        FitnCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(LucideIcons.user, size: 14, color: FitnColors.accent),
                  const SizedBox(width: 6),
                  Text('MUSCLE VOLUME ZONES', style: FitnText.microLabel),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                isImbalanced
                    ? '⚠ Top 3 muscles hold ${top3Share.round()}% of volume — consider rebalancing.'
                    : '✓ Balanced — top 3 muscles hold ${top3Share.round()}% of volume.',
                style: FitnText.serifItalic.copyWith(
                    fontSize: 10,
                    color: isImbalanced ? FitnColors.danger : FitnColors.success),
              ),
              const SizedBox(height: 12),
              // Muscle balance bars.
              ...sorted.map((z) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: FitnMacroBar(
                    label: z.muscle,
                    value: '${(z.totalVolumeKg / 1000).toStringAsFixed(1)}t (${z.balancePct.round()}%)',
                    percentage: z.balancePct,
                    color: _muscleColor(z.muscle),
                  ),
                );
              }),
            ],
          ),
        ),
        const SizedBox(height: 12),
        // Body map (simplified SVG).
        FitnCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('INTERACTIVE BODY MAP', style: FitnText.microLabel),
              const SizedBox(height: 8),
              SizedBox(
                height: 200,
                child: Stack(
                  children: [
                    // Simplified body silhouette.
                    Center(
                      child: CustomPaint(
                        size: const Size(120, 200),
                        painter: _BodyMapPainter(
                          zones: zones,
                          selectedMuscle: _selectedMuscle,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              // Muscle selector chips.
              Wrap(
                spacing: 4,
                runSpacing: 4,
                children: zones.take(8).map((z) {
                  final selected = _selectedMuscle == z.muscle;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedMuscle = z.muscle),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      color: selected ? FitnColors.accent : FitnColors.ink05,
                      child: Text(z.muscle.toUpperCase(),
                          style: GoogleFonts.inter(
                              fontSize: 8,
                              fontWeight: FontWeight.w700,
                              color: selected ? Colors.white : FitnColors.ink60)),
                    ),
                  );
                }).toList(),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Color _muscleColor(String muscle) {
    final lower = muscle.toLowerCase();
    if (['chest', 'triceps', 'shoulders', 'side deltoid'].contains(lower)) {
      return FitnColors.accent;
    }
    if (['lats', 'mid back', 'upper back', 'biceps'].contains(lower)) {
      return FitnColors.ink;
    }
    if (['quads', 'hamstrings'].contains(lower)) {
      return FitnColors.success;
    }
    return FitnColors.ink40;
  }

  // === EXERCISES sub-tab ===
  Widget _buildExercisesSubTab(List<ExerciseLog> logs) {
    final analyses = analyzeExerciseProgression(logs);
    final prs = calculatePersonalRecords(logs);
    final activeExNames = logs.map((e) => e.exerciseName).toSet().toList()..sort();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Quick set logger button.
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: () => setState(() => _isLogFormOpen = true),
            icon: Icon(LucideIcons.plus, size: 16, color: Colors.white),
            label: Text('LOG CUSTOM SET', style: FitnText.buttonLabel),
          ),
        ),
        const SizedBox(height: 12),

        // Personal records.
        FitnCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(LucideIcons.trophy, size: 14, color: FitnColors.accent),
                  const SizedBox(width: 6),
                  Text('PERSONAL RECORDS (1RM)', style: FitnText.microLabel),
                ],
              ),
              const SizedBox(height: 12),
              if (prs.isEmpty)
                Text('No PRs yet. Log sets to see your records.',
                    style: FitnText.serifItalic)
              else
                ...prs.take(10).map((pr) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(pr.exerciseName,
                              style: GoogleFonts.inter(
                                  fontSize: 11, fontWeight: FontWeight.w700)),
                        ),
                        Text('${pr.estimated1Rm.toStringAsFixed(1)} kg',
                            style: FitnText.mono.copyWith(
                                fontSize: 13,
                                color: FitnColors.accent,
                                fontWeight: FontWeight.w700)),
                      ],
                    ),
                  );
                }),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // Exercise progression analysis.
        FitnCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(LucideIcons.trendingUp, size: 14, color: FitnColors.accent),
                  const SizedBox(width: 6),
                  Text('EXERCISE PROGRESSION', style: FitnText.microLabel),
                ],
              ),
              const SizedBox(height: 12),
              // Exercise selector.
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                decoration: BoxDecoration(
                  color: FitnColors.fill,
                  border: Border.all(color: FitnColors.ink15, width: 1),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: activeExNames.contains(_selectedAnalysisEx)
                        ? _selectedAnalysisEx
                        : (activeExNames.isNotEmpty ? activeExNames.first : null),
                    isExpanded: true,
                    style: GoogleFonts.inter(fontSize: 11, color: FitnColors.ink),
                    items: activeExNames
                        .map((n) => DropdownMenuItem(value: n, child: Text(n)))
                        .toList(),
                    onChanged: (v) => setState(() => _selectedAnalysisEx = v ?? ''),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              // Selected exercise analysis.
              ...analyses.where((a) => a.exerciseName == _selectedAnalysisEx).map((a) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: _statCell('SESSIONS', '${a.sessions}'),
                        ),
                        Expanded(
                          child: _statCell('BEST 1RM', '${a.best1Rm.toStringAsFixed(1)} kg'),
                        ),
                        Expanded(
                          child: _statCell('CURRENT 1RM', '${a.current1Rm.toStringAsFixed(1)} kg'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text('First logged: ${_fmtDate(a.firstDate)}',
                        style: FitnText.monoSmall.copyWith(fontSize: 9)),
                    Text('Last logged: ${_fmtDate(a.lastDate)}',
                        style: FitnText.monoSmall.copyWith(fontSize: 9)),
                  ],
                );
              }),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // All exercises list.
        FitnCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('ALL EXERCISES (${analyses.length})', style: FitnText.microLabel),
              const SizedBox(height: 8),
              ...analyses.map((a) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    children: [
                      Container(
                        width: 20,
                        height: 20,
                        decoration: BoxDecoration(
                          color: FitnColors.ink05,
                          shape: BoxShape.circle,
                        ),
                        alignment: Alignment.center,
                        child: Text(a.targetMuscle.substring(0, 1).toUpperCase(),
                            style: GoogleFonts.inter(
                                fontSize: 8, fontWeight: FontWeight.w700)),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(a.exerciseName,
                            style: GoogleFonts.inter(fontSize: 11)),
                      ),
                      Text('${a.best1Rm.toStringAsFixed(0)} kg',
                          style: FitnText.mono.copyWith(
                              fontSize: 10, color: FitnColors.accent)),
                    ],
                  ),
                );
              }),
            ],
          ),
        ),

        // Log set modal.
        if (_isLogFormOpen) _buildLogSetModal(),
      ],
    );
  }

  Widget _buildLogSetModal() {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(20),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.ink, width: 1),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('LOG CUSTOM SET', style: FitnText.microLabel),
                  IconButton(
                    icon: Icon(LucideIcons.x, size: 16),
                    onPressed: () => setState(() => _isLogFormOpen = false),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Exercise picker — uses engine's 1,217-exercise database.
              Consumer(builder: (context, ref, _) {
                final categoriesAsync =
                    ref.watch(engineMuscleCategoriesProvider);
                final exercisesAsync =
                    ref.watch(exercisesByMuscleProvider(_logExMuscle));
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Muscle category chips (dynamic from engine).
                    categoriesAsync.when(
                      loading: () => const SizedBox(
                          height: 28,
                          child: Center(
                              child: SizedBox(
                                  width: 14,
                                  height: 14,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2)))),
                      error: (e, _) => Text('Error: $e',
                          style: FitnText.serifItalic),
                      data: (categories) => Wrap(
                        spacing: 4,
                        runSpacing: 4,
                        children: categories.map((c) {
                          final selected = _logExMuscle == c;
                          return GestureDetector(
                            onTap: () => setState(() {
                              _logExMuscle = c;
                            }),
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 4),
                              color: selected
                                  ? FitnColors.ink
                                  : FitnColors.ink05,
                              child: Text(c.toUpperCase(),
                                  style: GoogleFonts.inter(
                                      fontSize: 8,
                                      fontWeight: FontWeight.w700,
                                      color: selected
                                          ? Colors.white
                                          : FitnColors.ink60)),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Exercise dropdown (filtered by category from engine).
                    exercisesAsync.when(
                      loading: () => const SizedBox(
                          height: 40,
                          child: Center(
                              child: SizedBox(
                                  width: 14,
                                  height: 14,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2)))),
                      error: (e, _) => Text('Error: $e',
                          style: FitnText.serifItalic),
                      data: (exercises) {
                        if (exercises.isEmpty) {
                          return Text('No exercises in $_logExMuscle',
                              style: FitnText.serifItalic);
                        }
                        if (!exercises
                            .any((e) => e.name == _logExName)) {
                          _logExName = exercises.first.name;
                        }
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          decoration: BoxDecoration(
                            color: FitnColors.fill,
                            border: Border.all(
                                color: FitnColors.ink15, width: 1),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              value: _logExName,
                              isExpanded: true,
                              style: GoogleFonts.inter(
                                  fontSize: 11, color: FitnColors.ink),
                              items: exercises
                                  .map((e) => DropdownMenuItem(
                                        value: e.name,
                                        child: Text(
                                            '${e.name} (${e.equipment})',
                                            overflow: TextOverflow.ellipsis),
                                      ))
                                  .toList(),
                              onChanged: (v) => setState(
                                  () => _logExName = v ?? ''),
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                );
              }),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _logExWeightCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Weight (kg)', isDense: true),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _logExRepsCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Reps', isDense: true),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonHideUnderline(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        decoration: BoxDecoration(
                          color: FitnColors.fill,
                          border: Border.all(color: FitnColors.ink15, width: 1),
                        ),
                        child: DropdownButton<String>(
                          value: _logExType,
                          isExpanded: true,
                          style: GoogleFonts.inter(fontSize: 11, color: FitnColors.ink),
                          items: ['Normal', 'AMRAP', 'Failure', 'Drop Set']
                              .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                              .toList(),
                          onChanged: (v) => setState(() => _logExType = v ?? 'Normal'),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Row(
                    children: [
                      Checkbox(
                        value: _logExIsWarmUp,
                        onChanged: (v) => setState(() => _logExIsWarmUp = v ?? false),
                      ),
                      Text('Warm-up',
                          style: GoogleFonts.inter(fontSize: 10)),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _submitCustomSet,
                  style: ElevatedButton.styleFrom(backgroundColor: FitnColors.accent),
                  child: Text('LOG SET', style: FitnText.buttonLabel),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _submitCustomSet() {
    final weight = double.tryParse(_logExWeightCtrl.text);
    final reps = int.tryParse(_logExRepsCtrl.text);
    if (weight == null || reps == null || reps <= 0) return;

    final newSet = ExerciseSetLog(
      id: 'customset-${DateTime.now().millisecondsSinceEpoch}',
      weight: weight,
      reps: reps,
      isWarmUp: _logExIsWarmUp,
      type: _logExType,
    );
    final newLog = ExerciseLog(
      id: 'customex-${DateTime.now().millisecondsSinceEpoch}',
      exerciseName: _logExName,
      targetMuscle: _logExMuscle,
      date: DateTime.now(),
      sets: [newSet],
      durationMinutes: 10,
    );
    ref.read(appNotifierProvider.notifier).logExerciseSet(newLog);
    setState(() => _isLogFormOpen = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('💪 Logged: $weight kg × $reps reps for $_logExName!')),
    );
  }

  // === VISUALS sub-tab (flex/share cards) ===
  Widget _buildVisualsSubTab(
      List<ExerciseLog> logs,
      double lifetimeTons,
      LifetimeTier tier,
      double currentWeight,
      double weightDiff) {
    final coreMetrics = calculateCoreMetrics(logs);
    final prs = calculatePersonalRecords(logs);
    final topPr = prs.isNotEmpty ? prs.first : null;

    final cards = [
      _FlexCardData(
        id: 'tier',
        title: 'LIFETIME TIER',
        value: tier.name.toUpperCase(),
        subtitle: '$lifetimeTons tons lifted',
        color: FitnColors.accent,
      ),
      _FlexCardData(
        id: 'volume',
        title: 'TOTAL VOLUME',
        value: '${(coreMetrics.totalVolume / 1000).toStringAsFixed(1)}t',
        subtitle: '${coreMetrics.totalWorkingSets} working sets',
        color: FitnColors.ink,
      ),
      _FlexCardData(
        id: 'weight',
        title: 'WEIGHT JOURNEY',
        value: '${currentWeight.toStringAsFixed(1)} kg',
        subtitle: '${weightDiff >= 0 ? '+' : ''}${weightDiff.toStringAsFixed(1)} kg change',
        color: FitnColors.success,
      ),
      if (topPr != null)
        _FlexCardData(
          id: 'pr',
          title: 'TOP PR',
          value: '${topPr.estimated1Rm.toStringAsFixed(1)} kg',
          subtitle: topPr.exerciseName,
          color: FitnColors.warning,
        ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(LucideIcons.share2, size: 14, color: FitnColors.accent),
            const SizedBox(width: 6),
            Text('FLEX CARDS', style: FitnText.microLabel),
          ],
        ),
        const SizedBox(height: 8),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
          childAspectRatio: 0.85,
          children: cards.map((c) => _buildFlexCard(c)).toList(),
        ),
        if (_activeShareCard != null) _buildShareModal(_activeShareCard!),
      ],
    );
  }

  Widget _buildFlexCard(_FlexCardData data) {
    return GestureDetector(
      onTap: () => setState(() {
        _activeShareCard = data.id;
        _copiedShareText = false;
      }),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: data.color,
          border: Border.all(color: data.color, width: 1),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(data.title,
                style: GoogleFonts.inter(
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.0,
                    color: Colors.white70)),
            Text(data.value,
                style: FitnText.headline.copyWith(fontSize: 24, color: Colors.white)),
            Text(data.subtitle,
                style: GoogleFonts.inter(
                    fontSize: 9, color: Colors.white70, fontStyle: FontStyle.italic)),
            Align(
              alignment: Alignment.bottomRight,
              child: Icon(LucideIcons.share2, size: 14, color: Colors.white70),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildShareModal(String cardId) {
    final cards = <_FlexCardData>[];
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(20),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.ink, width: 1),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('SHARE FLEX CARD', style: FitnText.microLabel),
              const SizedBox(height: 12),
              Text('Card: $cardId',
                  style: FitnText.body),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () {
                  setState(() => _copiedShareText = true);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Copied to clipboard!')),
                  );
                },
                icon: Icon(LucideIcons.copy, size: 14, color: Colors.white),
                label: Text(_copiedShareText ? 'COPIED!' : 'COPY TEXT',
                    style: FitnText.buttonLabel),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () => setState(() => _activeShareCard = null),
                icon: Icon(LucideIcons.x, size: 14),
                label: Text('CLOSE',
                    style: GoogleFonts.inter(
                        fontSize: 11, fontWeight: FontWeight.w700)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // === Helpers ===
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
          Text(value,
              style: FitnText.mono.copyWith(
                  fontSize: 11,
                  color: accent ? FitnColors.accent : FitnColors.ink,
                  fontWeight: FontWeight.w700)),
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

  String _fmtDate(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Future<void> _showWeightDialog() async {
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
              onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
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

class _FlexCardData {
  _FlexCardData({
    required this.id,
    required this.title,
    required this.value,
    required this.subtitle,
    required this.color,
  });
  final String id;
  final String title;
  final String value;
  final String subtitle;
  final Color color;
}

/// Simplified body map painter — draws a silhouette with highlighted muscles.
class _BodyMapPainter extends CustomPainter {
  _BodyMapPainter({required this.zones, required this.selectedMuscle});
  final List<MuscleVolumeZone> zones;
  final String selectedMuscle;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = FitnColors.ink10
      ..style = PaintingStyle.fill;

    // Head.
    canvas.drawCircle(Offset(size.width / 2, 20), 14, paint);
    // Torso.
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width / 2 - 22, 36, 44, 80),
        const Radius.circular(8),
      ),
      paint,
    );
    // Arms.
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width / 2 - 36, 40, 12, 60),
        const Radius.circular(6),
      ),
      paint,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width / 2 + 24, 40, 12, 60),
        const Radius.circular(6),
      ),
      paint,
    );
    // Legs.
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width / 2 - 18, 120, 14, 60),
        const Radius.circular(6),
      ),
      paint,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width / 2 + 4, 120, 14, 60),
        const Radius.circular(6),
      ),
      paint,
    );

    // Highlight selected muscle.
    final highlight = Paint()
      ..color = FitnColors.accent
      ..style = PaintingStyle.fill;
    final lower = selectedMuscle.toLowerCase();
    if (lower == 'chest') {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(size.width / 2 - 18, 44, 36, 24),
          const Radius.circular(4),
        ),
        highlight,
      );
    } else if (['lats', 'mid back', 'upper back'].contains(lower)) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(size.width / 2 - 18, 70, 36, 24),
          const Radius.circular(4),
        ),
        highlight,
      );
    } else if (['quads'].contains(lower)) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(size.width / 2 - 16, 124, 12, 40),
          const Radius.circular(4),
        ),
        highlight,
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(size.width / 2 + 4, 124, 12, 40),
          const Radius.circular(4),
        ),
        highlight,
      );
    } else if (['shoulders', 'side deltoid'].contains(lower)) {
      canvas.drawCircle(Offset(size.width / 2 - 24, 44), 8, highlight);
      canvas.drawCircle(Offset(size.width / 2 + 24, 44), 8, highlight);
    } else if (['biceps'].contains(lower)) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(size.width / 2 - 34, 50, 8, 24),
          const Radius.circular(4),
        ),
        highlight,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _BodyMapPainter oldDelegate) =>
      oldDelegate.selectedMuscle != selectedMuscle;
}
