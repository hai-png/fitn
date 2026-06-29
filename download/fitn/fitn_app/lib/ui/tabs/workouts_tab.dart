/// Workouts tab. See spec §7.4.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class WorkoutsTab extends ConsumerWidget {
  const WorkoutsTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final plan = appState?.activePlan;

    if (plan == null) {
      return const Center(child: Text('No plan yet.'));
    }

    final training = plan.training;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Training Plan'),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.search),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                  builder: (_) => const ExerciseLibraryScreenWrapper()),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildHeader(training),
            const SizedBox(height: 16),
            _buildKpiGrid(training),
            if (training.muscleFocus.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildFocusChips(training.muscleFocus),
            ],
            const SizedBox(height: 16),
            _buildVolumeChart(training.weeklyVolumeSummary),
            const SizedBox(height: 16),
            ..._buildMesocycles(training),
            const SizedBox(height: 80),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          // Start workout session.
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Starting workout…')),
          );
        },
        icon: const Icon(LucideIcons.play),
        label: const Text('Start Workout'),
      ),
    );
  }

  Widget _buildHeader(TrainingPlan training) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('${training.totalDurationWeeks}-week program',
            style: const TextStyle(
                fontSize: 22, fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        Text(
          '${training.splitType.display} · ${training.trainingDaysPerWeek}d/wk · ${training.progression.display}',
          style: const TextStyle(color: AppColors.textSecondaryDark),
        ),
      ],
    );
  }

  Widget _buildKpiGrid(TrainingPlan training) {
    final exercises = training.mesocycles
        .expand((m) => m.microcycles)
        .expand((m) => m.workouts)
        .expand((w) => w.exercises)
        .map((e) => e.exercise.slug)
        .toSet();
    return Row(
      children: [
        Expanded(child: _KpiCell('Mesocycles', '${training.mesocycles.length}')),
        Expanded(
            child: _KpiCell(
                'Workouts',
                '${training.mesocycles.expand((m) => m.microcycles).expand((m) => m.workouts).length}')),
        Expanded(child: _KpiCell('Exercises', '${exercises.length}')),
      ],
    );
  }

  Widget _buildFocusChips(List<String> focus) {
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: focus
          .map((m) => Chip(
                label: Text(m),
                backgroundColor: AppColors.primary.withValues(alpha: 0.15),
                labelStyle: const TextStyle(color: AppColors.primary),
              ))
          .toList(),
    );
  }

  Widget _buildVolumeChart(Map<String, double> weeklyVolume) {
    final maxVol = weeklyVolume.values.fold(0.0, (a, b) => a > b ? a : b);
    final sorted = weeklyVolume.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Weekly Volume',
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            ...sorted.take(10).map((e) {
              final color = _muscleColor(e.key);
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    SizedBox(
                        width: 80,
                        child: Text(e.key,
                            style: const TextStyle(fontSize: 12))),
                    const SizedBox(width: 8),
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: maxVol > 0 ? e.value / maxVol : 0,
                          minHeight: 10,
                          color: color,
                          backgroundColor: color.withValues(alpha: 0.15),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                        width: 32,
                        child: Text(e.value.toStringAsFixed(0),
                            style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w500))),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  List<Widget> _buildMesocycles(TrainingPlan training) {
    final widgets = <Widget>[];
    for (var i = 0; i < training.mesocycles.length; i++) {
      final meso = training.mesocycles[i];
      widgets.add(_MesocycleCard(mesocycle: meso, initiallyExpanded: i == 0));
      widgets.add(const SizedBox(height: 12));
    }
    return widgets;
  }

  Color _muscleColor(String muscle) {
    final lower = muscle.toLowerCase();
    if (['chest', 'triceps', 'shoulders', 'side_delts'].contains(lower)) {
      return AppColors.primary;
    }
    if (['back', 'lats', 'biceps', 'rear_delts'].contains(lower)) {
      return AppColors.accent;
    }
    if (['quads', 'hamstrings', 'glutes', 'calves'].contains(lower)) {
      return AppColors.info;
    }
    if (['abs', 'obliques', 'core'].contains(lower)) {
      return const Color(0xFFEAB308);
    }
    return const Color(0xFFF43F5E);
  }
}

class _KpiCell extends StatelessWidget {
  const _KpiCell(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: const TextStyle(
                fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.primary)),
        const SizedBox(height: 2),
        Text(label,
            style: const TextStyle(
                color: AppColors.textSecondaryDark, fontSize: 11)),
      ],
    );
  }
}

class _MesocycleCard extends StatefulWidget {
  const _MesocycleCard({required this.mesocycle, this.initiallyExpanded = false});
  final Mesocycle mesocycle;
  final bool initiallyExpanded;

  @override
  State<_MesocycleCard> createState() => _MesocycleCardState();
}

class _MesocycleCardState extends State<_MesocycleCard> {
  late bool _expanded = widget.initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          ListTile(
            title: Text(widget.mesocycle.name,
                style:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            subtitle: Text(
                '${widget.mesocycle.durationWeeks}w · ${widget.mesocycle.progression.display}'),
            trailing: IconButton(
              icon: Icon(_expanded ? LucideIcons.chevronUp : LucideIcons.chevronDown),
              onPressed: () => setState(() => _expanded = !_expanded),
            ),
            onTap: () => setState(() => _expanded = !_expanded),
          ),
          if (_expanded)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Column(
                children: widget.mesocycle.microcycles
                    .expand((m) => m.workouts)
                    .map((w) => _WorkoutCard(workout: w))
                    .toList(),
              ),
            ),
        ],
      ),
    );
  }
}

class _WorkoutCard extends StatefulWidget {
  const _WorkoutCard({required this.workout});
  final Workout workout;

  @override
  State<_WorkoutCard> createState() => _WorkoutCardState();
}

class _WorkoutCardState extends State<_WorkoutCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final w = widget.workout;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Column(
        children: [
          ListTile(
            leading: CircleAvatar(
              backgroundColor: AppColors.primary.withValues(alpha: 0.15),
              child: Text('${w.dayNumber}',
                  style: const TextStyle(
                      color: AppColors.primary, fontWeight: FontWeight.w600)),
            ),
            title: Text(w.name, style: const TextStyle(fontWeight: FontWeight.w500)),
            subtitle: Text(
                '${w.exercises.length} exercises · ${w.estimatedDurationMin} min'),
            trailing: IconButton(
              icon: Icon(_expanded
                  ? LucideIcons.chevronUp
                  : LucideIcons.chevronDown),
              onPressed: () => setState(() => _expanded = !_expanded),
            ),
            onTap: () => setState(() => _expanded = !_expanded),
          ),
          if (_expanded)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: w.exercises
                    .map((e) => _ExerciseRow(exercise: e))
                    .toList(),
              ),
            ),
        ],
      ),
    );
  }
}

class _ExerciseRow extends StatelessWidget {
  const _ExerciseRow({required this.exercise});
  final WorkoutExercise exercise;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      leading: ClipRRect(
        borderRadius: BorderRadius.circular(6),
        child: exercise.exercise.videoThumbnail != null &&
                exercise.exercise.videoThumbnail!.isNotEmpty
            ? Image.network(exercise.exercise.videoThumbnail!,
                width: 48, height: 48, fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(
                    width: 48,
                    height: 48,
                    color: AppColors.bgDarkSurface,
                    child: const Icon(LucideIcons.dumbbell, size: 18)))
            : Container(
                width: 48,
                height: 48,
                color: AppColors.bgDarkSurface,
                child: const Icon(LucideIcons.dumbbell, size: 18),
              ),
      ),
      title: Text(exercise.exercise.name,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
      subtitle: Text(
        '${exercise.sets} × ${exercise.reps} · ${exercise.restSec}s rest · RPE ${exercise.rpeTarget?.toStringAsFixed(1) ?? "—"}',
        style: const TextStyle(color: AppColors.textSecondaryDark, fontSize: 11),
      ),
      trailing: exercise.category == ExerciseCategory.compoundPrimary
          ? Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text('Compound',
                  style: TextStyle(
                      color: AppColors.primary, fontSize: 10)),
            )
          : null,
      onTap: () {
        // Show exercise detail sheet.
        showModalBottomSheet(
          context: context,
          builder: (_) => _ExerciseDetailSheet(exercise: exercise),
        );
      },
    );
  }
}

class _ExerciseDetailSheet extends StatelessWidget {
  const _ExerciseDetailSheet({required this.exercise});
  final WorkoutExercise exercise;

  @override
  Widget build(BuildContext context) {
    final e = exercise.exercise;
    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return ListView(
          controller: scrollController,
          padding: const EdgeInsets.all(16),
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.bgDarkSurface,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(e.name,
                style: const TextStyle(
                    fontSize: 22, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                _metaChip('Category', exercise.category.display),
                _metaChip('Mechanics', e.mechanics),
                _metaChip('Force', e.forceType),
                _metaChip('Equipment', e.equipment),
                _metaChip('Level', e.experienceLevel.display),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _DetailCell('Sets', '${exercise.sets}'),
                _DetailCell('Reps', exercise.reps),
                _DetailCell('Rest', '${exercise.restSec}s'),
                _DetailCell('RPE',
                    exercise.rpeTarget?.toStringAsFixed(1) ?? '—'),
              ],
            ),
            const SizedBox(height: 16),
            if (e.videoThumbnail != null && e.videoThumbnail!.isNotEmpty)
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.network(e.videoThumbnail!,
                    height: 180, width: double.infinity,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                        height: 180,
                        color: AppColors.bgDarkSurface,
                        child: const Center(child: Icon(LucideIcons.image)))),
              ),
            const SizedBox(height: 16),
            const Text('Overview',
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Text(e.overview),
            const SizedBox(height: 16),
            const Text('Instructions',
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            ...e.instructions.asMap().entries.map((entry) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 10,
                      backgroundColor: AppColors.primary,
                      child: Text('${entry.key + 1}',
                          style: const TextStyle(
                              fontSize: 10, color: Colors.white)),
                    ),
                    const SizedBox(width: 8),
                    Expanded(child: Text(entry.value)),
                  ],
                ),
              );
            }),
            if (e.tips.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text('Pro Tips',
                  style:
                      TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              ...e.tips.map((t) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(LucideIcons.lightbulb,
                            size: 16, color: AppColors.accent),
                        const SizedBox(width: 8),
                        Expanded(child: Text(t)),
                      ],
                    ),
                  )),
            ],
          ],
        );
      },
    );
  }

  Widget _metaChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.bgDarkSurface,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text('$label: $value',
          style: const TextStyle(
              fontSize: 11, color: AppColors.textSecondaryDark)),
    );
  }
}

class _DetailCell extends StatelessWidget {
  const _DetailCell(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.bgDarkSurface,
          borderRadius: BorderRadius.circular(8),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 2),
        child: Column(
          children: [
            Text(value,
                style: const TextStyle(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            Text(label,
                style: const TextStyle(
                    color: AppColors.textSecondaryDark, fontSize: 10)),
          ],
        ),
      ),
    );
  }
}

/// Re-export the exercise library screen for navigation from Workouts tab.
class ExerciseLibraryScreenWrapper extends StatelessWidget {
  const ExerciseLibraryScreenWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: Text('Exercise Library')));
  }
}
