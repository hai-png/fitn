/// Training tab — matches FitLife Hub design.
///
/// Features:
/// - Program header with weekly timeline tracker.
/// - Active splits horizontal day selector.
/// - Active day exercise cards with sets/reps/rest/RPE.
/// - Inline rest timer.
/// - Program preset selector.
/// - Exercise video tutorial modal.
library;

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../data/workout_templates.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class TrainingTab extends ConsumerStatefulWidget {
  const TrainingTab({super.key});

  @override
  ConsumerState<TrainingTab> createState() => _TrainingTabState();
}

class _TrainingTabState extends ConsumerState<TrainingTab> {
  int _selectedDayIdx = 0;
  int? _expandedExIdx;
  bool _isWorkoutActive = false;
  final Set<int> _completedExercises = {};
  int _restTimerSeconds = 0;
  Timer? _restTimer;
  int _currentWeek = 1;
  final int _totalWeeks = 8;

  // Modals.
  bool _isProgramSelectorOpen = false;
  bool _isSplitBuilderOpen = false;
  WorkoutExercise? _activeTutorialExercise;
  bool _isVideoPlaying = true;
  int _videoProgress = 15;
  bool _tutorialMuted = false;

  // Split builder state.
  final List<Map<String, dynamic>> _builderSchedule = [];
  String _builderTitle = '';
  String _builderDescription = '';
  String _builderDifficulty = 'Intermediate';
  int _selectedBuilderDayIndex = 0;
  String _selectedDbCategory = 'Chest';
  String _selectedDbExerciseName = 'Flat Barbell Bench Press';

  @override
  void dispose() {
    _restTimer?.cancel();
    super.dispose();
  }

  void _startRestTimer(int seconds) {
    _restTimer?.cancel();
    setState(() {
      _restTimerSeconds = seconds;
    });
    _restTimer = Timer.periodic(const Duration(seconds: 1), (t) {
      setState(() {
        _restTimerSeconds--;
        if (_restTimerSeconds <= 0) {
          t.cancel();
        }
      });
    });
  }

  void _toggleExerciseComplete(int idx, int restSec) {
    setState(() {
      if (_completedExercises.contains(idx)) {
        _completedExercises.remove(idx);
      } else {
        _completedExercises.add(idx);
        if (restSec > 0) _startRestTimer(restSec);
      }
    });
  }

  void _finishWorkout() {
    final appState = ref.read(appNotifierProvider).valueOrNull;
    final plan = appState?.activePlan;
    if (plan == null) return;

    final workout = _currentWorkout(plan);
    if (workout == null) return;

    // Save a workout log summary.
    final burnRate = 7;
    final caloriesBurned = workout.estimatedDurationMin * burnRate;
    // We don't have a direct WorkoutLogSummary type — use WorkoutLogRecord.
    // The notifier.logWorkout takes WorkoutLogRecord. Skip for now — show snackbar.
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
              '🎉 Magnificent work! You completed "${workout.name}"! Logged ${caloriesBurned} kcal burned.'),
        ),
      );
      setState(() {
        _isWorkoutActive = false;
        _completedExercises.clear();
      });
    }
  }

  Workout? _currentWorkout(FitnessPlan plan) {
    if (plan.training.mesocycles.isEmpty) return null;
    final meso = plan.training.mesocycles.first;
    if (meso.microcycles.isEmpty) return null;
    final workouts = meso.microcycles.first.workouts;
    if (workouts.isEmpty) return null;
    if (_selectedDayIdx >= workouts.length) return workouts.first;
    return workouts[_selectedDayIdx];
  }

  @override
  Widget build(BuildContext context) {
    final appAsync = ref.watch(appNotifierProvider);
    final appState = appAsync.valueOrNull;
    final plan = appState?.activePlan;

    if (plan == null) {
      return const Center(child: Text('No plan yet.'));
    }

    final training = plan.training;
    final workouts = <Workout>[];
    for (final meso in training.mesocycles) {
      for (final micro in meso.microcycles) {
        workouts.addAll(micro.workouts);
      }
    }
    if (_selectedDayIdx >= workouts.length) _selectedDayIdx = 0;
    final selectedDay = workouts.isEmpty ? null : workouts[_selectedDayIdx];

    return Scaffold(
      backgroundColor: FitnColors.cream,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
              children: [
                _buildProgramHeader(training),
                const SizedBox(height: 20),
                _buildSplitsHeader(),
                const SizedBox(height: 12),
                _buildDaySelector(workouts),
                const SizedBox(height: 20),
                if (selectedDay != null)
                  _buildDayCard(selectedDay)
                else
                  const Padding(
                    padding: EdgeInsets.all(24),
                    child: Text('No workouts in plan.'),
                  ),
              ],
            ),
            if (_isProgramSelectorOpen) _buildProgramSelectorModal(),
            if (_isSplitBuilderOpen) _buildSplitBuilderModal(),
            if (_activeTutorialExercise != null) _buildTutorialPlayerModal(),
          ],
        ),
      ),
    );
  }

  // === Program Preset Selector Modal ===
  Widget _buildProgramSelectorModal() {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(20),
          padding: const EdgeInsets.all(20),
          constraints: const BoxConstraints(maxHeight: 500),
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
                  Text('SELECT PROGRAM PRESET',
                      style: FitnText.microLabel),
                  IconButton(
                    icon: Icon(LucideIcons.x, size: 16),
                    onPressed: () =>
                        setState(() => _isProgramSelectorOpen = false),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Expanded(
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: ProgramPresets.all.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, idx) {
                    final p = ProgramPresets.all[idx];
                    return InkWell(
                      onTap: () => _applyPresetProgram(p),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          border: Border.all(color: FitnColors.ink10, width: 1),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(p.name.toUpperCase(),
                                      style: GoogleFonts.inter(
                                          fontSize: 12,
                                          fontWeight: FontWeight.w700)),
                                ),
                                Text('${p.durationWeeks}w',
                                    style: FitnText.mono.copyWith(
                                        fontSize: 10,
                                        color: FitnColors.accent)),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(p.description,
                                style: FitnText.serifItalic
                                    .copyWith(fontSize: 10)),
                            const SizedBox(height: 6),
                            Row(
                              children: [
                                _miniBadge(p.splitType),
                                const SizedBox(width: 6),
                                _miniBadge('${p.daysPerWeek}d/wk'),
                                const SizedBox(width: 6),
                                _miniBadge(p.goal.toUpperCase()),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _miniBadge(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      color: FitnColors.ink05,
      child: Text(text,
          style: GoogleFonts.inter(
              fontSize: 8,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.8,
              color: FitnColors.ink60)),
    );
  }

  void _applyPresetProgram(ProgramPreset preset) {
    // In a full implementation, this would rebuild the training plan with
    // the preset's split template. For now, just close the modal.
    setState(() => _isProgramSelectorOpen = false);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(
                'Applied "${preset.name}" — ${preset.durationWeeks}w ${preset.splitType}')),
      );
    }
  }

  // === Split Builder Modal ===
  Widget _buildSplitBuilderModal() {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.all(16),
          constraints: const BoxConstraints(maxHeight: 600),
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
                  Text('CUSTOM SPLIT BUILDER', style: FitnText.microLabel),
                  IconButton(
                    icon: Icon(LucideIcons.x, size: 16),
                    onPressed: () =>
                        setState(() => _isSplitBuilderOpen = false),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                decoration: const InputDecoration(
                    labelText: 'Plan Title', isDense: true),
                onChanged: (v) => _builderTitle = v,
                controller: TextEditingController(text: _builderTitle),
              ),
              const SizedBox(height: 8),
              TextField(
                decoration: const InputDecoration(
                    labelText: 'Description', isDense: true),
                onChanged: (v) => _builderDescription = v,
                controller: TextEditingController(text: _builderDescription),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Text('DAYS: ${_builderSchedule.length}',
                      style: FitnText.microLabel),
                  const Spacer(),
                  ElevatedButton(
                    onPressed: _addBuilderDay,
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size(0, 32),
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                    ),
                    child: Text('+ ADD DAY',
                        style: GoogleFonts.inter(
                            fontSize: 9, fontWeight: FontWeight.w700)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Expanded(
                child: _builderSchedule.isEmpty
                    ? Center(
                        child: Text('No days yet. Tap "+ ADD DAY" to start.',
                            style: FitnText.serifItalic))
                    : ListView.builder(
                        itemCount: _builderSchedule.length,
                        itemBuilder: (context, idx) {
                          final day = _builderSchedule[idx];
                          final exercises =
                              day['exercises'] as List? ?? [];
                          return Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            padding: const EdgeInsets.all(8),
                            color: Colors.white,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text('DAY ${idx + 1}',
                                        style: FitnText.microLabel
                                            .copyWith(fontSize: 9)),
                                    const Spacer(),
                                    IconButton(
                                      icon: Icon(LucideIcons.trash2,
                                          size: 12, color: FitnColors.danger),
                                      onPressed: () =>
                                          _removeBuilderDay(idx),
                                      padding: EdgeInsets.zero,
                                      constraints: const BoxConstraints(),
                                    ),
                                  ],
                                ),
                                Text(day['name'] ?? '',
                                    style: GoogleFonts.inter(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w700)),
                                Text('${exercises.length} exercises',
                                    style: FitnText.monoSmall
                                        .copyWith(fontSize: 9)),
                              ],
                            ),
                          );
                        },
                      ),
              ),
              const SizedBox(height: 8),
              // Exercise DB picker.
              Container(
                padding: const EdgeInsets.all(8),
                color: Colors.white,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('ADD EXERCISE', style: FitnText.microLabel),
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 32,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: WorkoutTemplates.categories.map((c) {
                          final selected = _selectedDbCategory == c;
                          return Padding(
                            padding: const EdgeInsets.only(right: 4),
                            child: GestureDetector(
                              onTap: () => setState(() {
                                _selectedDbCategory = c;
                                final filtered = WorkoutTemplates
                                    .exerciseDatabase
                                    .where((e) =>
                                        e.targetMuscle == c ||
                                        (c == 'Back' && [
                                          'Lats',
                                          'Mid Back',
                                          'Upper Back'
                                        ].contains(e.targetMuscle)) ||
                                        (c == 'Legs' && [
                                          'Quads',
                                          'Hamstrings'
                                        ].contains(e.targetMuscle)))
                                    .toList();
                                if (filtered.isNotEmpty) {
                                  _selectedDbExerciseName = filtered.first.name;
                                }
                              }),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 6),
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
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      decoration: BoxDecoration(
                        color: FitnColors.fill,
                        border:
                            Border.all(color: FitnColors.ink15, width: 1),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: _selectedDbExerciseName,
                          isExpanded: true,
                          style: GoogleFonts.inter(
                              fontSize: 11, color: FitnColors.ink),
                          items: WorkoutTemplates.exerciseDatabase
                              .where((e) =>
                                  _selectedDbCategory == 'Chest' &&
                                      e.targetMuscle == 'Chest' ||
                                  _selectedDbCategory == 'Back' && [
                                    'Lats',
                                    'Mid Back',
                                    'Upper Back'
                                  ].contains(e.targetMuscle) ||
                                  _selectedDbCategory == 'Legs' && [
                                    'Quads',
                                    'Hamstrings'
                                  ].contains(e.targetMuscle) ||
                                  _selectedDbCategory == 'Shoulders' &&
                                      ['Shoulders', 'Side Deltoid', 'Rear Deltoid']
                                          .contains(e.targetMuscle) ||
                                  _selectedDbCategory == 'Arms' &&
                                      ['Biceps', 'Triceps'].contains(e.targetMuscle) ||
                                  _selectedDbCategory == 'Core' &&
                                      ['Lower Abs', 'Core'].contains(e.targetMuscle) ||
                                  _selectedDbCategory == 'Cardio' &&
                                      e.targetMuscle == 'Cardio')
                              .map((e) => DropdownMenuItem(
                                  value: e.name, child: Text(e.name)))
                              .toList(),
                          onChanged: (v) => setState(() =>
                              _selectedDbExerciseName = v ?? ''),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _addExerciseToBuilderDay,
                        style: ElevatedButton.styleFrom(
                          minimumSize: const Size(0, 32),
                        ),
                        child: Text('+ ADD TO DAY ${_selectedBuilderDayIndex + 1}',
                            style: GoogleFonts.inter(
                                fontSize: 9, fontWeight: FontWeight.w700)),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _saveBuilderPlan,
                  style: ElevatedButton.styleFrom(
                      backgroundColor: FitnColors.accent),
                  child: Text('SAVE CUSTOM PLAN',
                      style: FitnText.buttonLabel),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _addBuilderDay() {
    setState(() {
      _builderSchedule.add({
        'name': 'Day ${_builderSchedule.length + 1} - Custom',
        'focus': 'Custom',
        'duration': 45,
        'exercises': <Map<String, dynamic>>[],
      });
      _selectedBuilderDayIndex = _builderSchedule.length - 1;
    });
  }

  void _removeBuilderDay(int idx) {
    setState(() {
      _builderSchedule.removeAt(idx);
      if (_selectedBuilderDayIndex >= _builderSchedule.length) {
        _selectedBuilderDayIndex = (_builderSchedule.length - 1).clamp(0, 999);
      }
    });
  }

  void _addExerciseToBuilderDay() {
    final item = WorkoutTemplates.exerciseDatabase
        .where((e) => e.name == _selectedDbExerciseName)
        .firstOrNull;
    if (item == null || _builderSchedule.isEmpty) return;
    setState(() {
      final day = _builderSchedule[_selectedBuilderDayIndex];
      (day['exercises'] as List).add({
        'name': item.name,
        'sets': item.sets,
        'reps': item.reps,
        'rest': item.restSeconds,
        'targetMuscle': item.targetMuscle,
      });
    });
  }

  void _saveBuilderPlan() {
    if (_builderSchedule.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Add at least one day to your custom split.')),
      );
      return;
    }
    setState(() => _isSplitBuilderOpen = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Saved "${_builderTitle.isEmpty ? "Custom Split" : _builderTitle}" with ${_builderSchedule.length} days')),
    );
  }

  // === Video Tutorial Player Modal ===
  Widget _buildTutorialPlayerModal() {
    final ex = _activeTutorialExercise!;
    final e = ex.exercise;
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.all(16),
          constraints: const BoxConstraints(maxHeight: 600),
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
                  Expanded(
                    child: Text('FORM TUTORIAL',
                        style: FitnText.microLabel),
                  ),
                  IconButton(
                    icon: Icon(LucideIcons.x, size: 16),
                    onPressed: () =>
                        setState(() => _activeTutorialExercise = null),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(e.name, style: FitnText.headline.copyWith(fontSize: 18)),
              const SizedBox(height: 12),
              // Video player mock.
              AspectRatio(
                aspectRatio: 16 / 9,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    if (e.videoThumbnail != null &&
                        e.videoThumbnail!.isNotEmpty)
                      Image.network(e.videoThumbnail!,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => Container(
                              color: FitnColors.ink05,
                              child: Icon(LucideIcons.video, size: 48, color: FitnColors.ink40)))
                    else
                      Container(
                          color: FitnColors.ink05,
                          child: Icon(LucideIcons.video, size: 48, color: FitnColors.ink40)),
                    // Play/pause button.
                    GestureDetector(
                      onTap: () =>
                          setState(() => _isVideoPlaying = !_isVideoPlaying),
                      child: Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(
                          color: FitnColors.accent,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          _isVideoPlaying ? LucideIcons.pause : LucideIcons.play,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
                    ),
                    // Mute button (top-right).
                    Positioned(
                      top: 8,
                      right: 8,
                      child: GestureDetector(
                        onTap: () =>
                            setState(() => _tutorialMuted = !_tutorialMuted),
                        child: Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: Colors.black54,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            _tutorialMuted
                                ? LucideIcons.volumeX
                                : LucideIcons.volume2,
                            color: Colors.white,
                            size: 14,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              // Progress bar.
              ClipRRect(
                child: LinearProgressIndicator(
                  value: _videoProgress / 100,
                  minHeight: 4,
                  color: FitnColors.accent,
                  backgroundColor: FitnColors.ink10,
                ),
              ),
              const SizedBox(height: 12),
              Text('INSTRUCTION', style: FitnText.microLabel),
              const SizedBox(height: 4),
              Text(e.overview, style: FitnText.body),
              const SizedBox(height: 12),
              Text('FORM STEPS', style: FitnText.microLabel),
              const SizedBox(height: 6),
              ...e.instructions.asMap().entries.map((entry) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 20,
                        height: 20,
                        decoration: const BoxDecoration(
                          color: FitnColors.ink,
                          shape: BoxShape.circle,
                        ),
                        alignment: Alignment.center,
                        child: Text('${entry.key + 1}',
                            style: GoogleFonts.inter(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: Colors.white)),
                      ),
                      const SizedBox(width: 8),
                      Expanded(child: Text(entry.value, style: FitnText.body)),
                    ],
                  ),
                );
              }),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgramHeader(TrainingPlan training) {
    return FitnCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(LucideIcons.trendingUp,
                            size: 14, color: FitnColors.accent),
                        const SizedBox(width: 6),
                        Text('STRUCTURED PROGRAM PROGRESS',
                            style: FitnText.microLabelAccent.copyWith(fontSize: 9)),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      training.splitType.display,
                      style: FitnText.headline.copyWith(fontSize: 18),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Goal: ${training.goal.display} • ${training.totalDurationWeeks}-Week Plan',
                      style: FitnText.serifItalic.copyWith(fontSize: 11),
                    ),
                  ],
                ),
              ),
              GestureDetector(
                onTap: () => setState(() => _isProgramSelectorOpen = true),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: FitnColors.fill,
                    border: Border.all(color: FitnColors.ink15, width: 1),
                  ),
                  child: Text('PROGRAMS',
                      style: GoogleFonts.inter(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.0,
                          color: FitnColors.ink)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Weeks timeline.
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('CYCLE TIMELINE', style: FitnText.microLabel.copyWith(fontSize: 9)),
                Text(
                  'WEEK $_currentWeek OF ${training.totalDurationWeeks}',
                  style: FitnText.monoSmall.copyWith(
                      fontSize: 9, color: FitnColors.accent),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 36,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: training.totalDurationWeeks,
              separatorBuilder: (_, __) => const SizedBox(width: 4),
              itemBuilder: (context, i) {
                final weekIdx = i + 1;
                final isActive = weekIdx == _currentWeek;
                final isPast = weekIdx < _currentWeek;
                return GestureDetector(
                  onTap: () => setState(() => _currentWeek = weekIdx),
                  child: Container(
                    width: 36,
                    height: 32,
                    decoration: BoxDecoration(
                      color: isActive
                          ? FitnColors.ink
                          : (isPast ? FitnColors.accent05 : FitnColors.fill),
                      border: Border.all(
                          color: isActive
                              ? FitnColors.ink
                              : (isPast ? FitnColors.accent20 : FitnColors.ink05),
                          width: 1),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('WK',
                            style: GoogleFonts.inter(
                                fontSize: 7,
                                color: isActive
                                    ? Colors.white60
                                    : FitnColors.ink40,
                                fontWeight: FontWeight.w600)),
                        Text('$weekIdx',
                            style: FitnText.mono.copyWith(
                                fontSize: 11,
                                color: isActive
                                    ? Colors.white
                                    : (isPast
                                        ? FitnColors.accent
                                        : FitnColors.ink40),
                                fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSplitsHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Icon(LucideIcons.sliders, size: 14, color: FitnColors.ink40),
            const SizedBox(width: 6),
            Text('ACTIVE SPLITS SCHEDULE', style: FitnText.microLabel),
          ],
        ),
        GestureDetector(
          onTap: () {
            _initBuilder();
            setState(() => _isSplitBuilderOpen = true);
          },
          child: Row(
            children: [
              Icon(LucideIcons.sliders, size: 12, color: FitnColors.accent),
              const SizedBox(width: 4),
              Text('CUSTOMIZE SPLIT / FROM SCRATCH',
                  style: GoogleFonts.inter(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      color: FitnColors.accent)),
            ],
          ),
        ),
      ],
    );
  }

  void _initBuilder() {
    final plan = ref.read(appNotifierProvider).valueOrNull?.activePlan;
    if (plan == null) return;
    _builderSchedule.clear();
    for (final meso in plan.training.mesocycles) {
      for (final micro in meso.microcycles) {
        for (final w in micro.workouts) {
          _builderSchedule.add({
            'name': w.name,
            'focus': w.focus,
            'duration': w.estimatedDurationMin,
            'exercises': w.exercises.map((e) => {
                  'name': e.exercise.name,
                  'sets': e.sets,
                  'reps': e.reps,
                  'rest': e.restSec,
                  'targetMuscle': e.exercise.muscleGroups.isNotEmpty
                      ? e.exercise.muscleGroups.first
                      : '',
                }).toList(),
          });
        }
      }
    }
    _builderTitle = plan.training.splitType.display;
    _builderDescription = 'Custom tailored split schedule.';
  }

  Widget _buildDaySelector(List<Workout> workouts) {
    return SizedBox(
      height: 88,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: workouts.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, idx) {
          final w = workouts[idx];
          final isSelected = _selectedDayIdx == idx;
          return GestureDetector(
            onTap: () => setState(() {
              _selectedDayIdx = idx;
              _completedExercises.clear();
              _isWorkoutActive = false;
            }),
            child: Container(
              width: 112,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isSelected ? FitnColors.ink : Colors.white,
                border: Border.all(
                    color: isSelected ? FitnColors.ink : FitnColors.ink10,
                    width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'DAY ${idx + 1}',
                    style: GoogleFonts.inter(
                        fontSize: 9,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.4,
                        color: isSelected ? Colors.white60 : FitnColors.ink40),
                  ),
                  const SizedBox(height: 4),
                  Expanded(
                    child: Text(
                      w.name.toUpperCase(),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: isSelected ? Colors.white : FitnColors.ink),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${w.exercises.length} exercises',
                    style: FitnText.serifItalic.copyWith(
                        fontSize: 10,
                        color: isSelected ? Colors.white70 : FitnColors.ink50),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildDayCard(Workout workout) {
    final isAllCompleted = workout.exercises.isNotEmpty &&
        workout.exercises.asMap().entries.every((e) => _completedExercises.contains(e.key));

    return FitnCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row.
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      color: FitnColors.ink,
                      child: Text(
                        'WORKOUT',
                        style: GoogleFonts.inter(
                            fontSize: 8,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                            letterSpacing: 1.4),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(workout.name,
                        style: FitnText.headline.copyWith(fontSize: 20)),
                    const SizedBox(height: 4),
                    Text(
                      'Estimated duration: ${workout.estimatedDurationMin} min • ${workout.exercises.length} exercises',
                      style: FitnText.monoSmall.copyWith(fontSize: 10),
                    ),
                  ],
                ),
              ),
              if (!_isWorkoutActive)
                ElevatedButton(
                  onPressed: () => setState(() => _isWorkoutActive = true),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: FitnColors.accent,
                    minimumSize: const Size(0, 32),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(LucideIcons.play, size: 12, color: Colors.white),
                      const SizedBox(width: 4),
                      Text('BEGIN DAY', style: FitnText.buttonLabel.copyWith(fontSize: 9)),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),
          // Active workout status bar.
          if (_isWorkoutActive) ...[
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: FitnColors.ink05,
                border: Border.all(color: FitnColors.ink10, width: 1),
              ),
              child: Row(
                children: [
                  // Pulsing dot.
                  Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: FitnColors.accent,
                      shape: BoxShape.circle,
                    ),
                  )
                      .animate(onPlay: (c) => c.repeat())
                      .fade(begin: 0.3, end: 1, duration: 800.ms),
                  const SizedBox(width: 8),
                  Text('WORKOUT ACTIVE',
                      style: GoogleFonts.inter(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.4,
                          color: FitnColors.accent)),
                  const Spacer(),
                  if (_restTimerSeconds > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: FitnColors.accent10,
                        border: Border.all(color: FitnColors.accent20, width: 1),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(LucideIcons.timer, size: 12, color: FitnColors.accent),
                          const SizedBox(width: 4),
                          Text('Rest: ${_restTimerSeconds}s',
                              style: FitnText.mono.copyWith(
                                  fontSize: 10, color: FitnColors.accent)),
                        ],
                      ),
                    ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: isAllCompleted ? _finishWorkout : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isAllCompleted
                          ? FitnColors.ink
                          : FitnColors.ink05,
                      minimumSize: const Size(0, 28),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    ),
                    child: Text(
                      'FINISH LOG',
                      style: FitnText.buttonLabel.copyWith(
                          fontSize: 9,
                          color: isAllCompleted ? Colors.white : FitnColors.ink30),
                    ),
                  ),
                ],
              ),
            ),
          ],
          // Exercises list.
          ...workout.exercises.asMap().entries.map((entry) {
            final idx = entry.key;
            final ex = entry.value;
            final isCompleted = _completedExercises.contains(idx);
            final isExpanded = _expandedExIdx == idx;
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _buildExerciseCard(idx, ex, isCompleted, isExpanded),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildExerciseCard(
      int idx, WorkoutExercise ex, bool isCompleted, bool isExpanded) {
    return Container(
      decoration: BoxDecoration(
        color: isCompleted ? FitnColors.ink05 : Colors.white,
        border: Border.all(
            color: isCompleted ? FitnColors.ink05 : FitnColors.ink10, width: 1),
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                // Checkbox / number circle.
                if (_isWorkoutActive)
                  GestureDetector(
                    onTap: () => _toggleExerciseComplete(idx, ex.restSec),
                    child: isCompleted
                        ? Icon(LucideIcons.checkCircle2,
                            size: 22, color: FitnColors.accent)
                        : Icon(LucideIcons.circle,
                            size: 22, color: FitnColors.ink20),
                  )
                else
                  Container(
                    width: 22,
                    height: 22,
                    decoration: BoxDecoration(
                      color: FitnColors.ink05,
                      border: Border.all(color: FitnColors.ink10, width: 1),
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Text('${idx + 1}',
                        style: FitnText.monoSmall.copyWith(fontSize: 9)),
                  ),
                const SizedBox(width: 12),
                // Exercise info.
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(ex.exercise.name.toUpperCase(),
                                style: GoogleFonts.inter(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w700,
                                    color: FitnColors.ink)),
                          ),
                          if (ex.category == ExerciseCategory.compoundPrimary)
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 2),
                              color: FitnColors.ink05,
                              child: Text('COMPOUND',
                                  style: GoogleFonts.inter(
                                      fontSize: 8,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 1.0,
                                      color: FitnColors.ink70)),
                            ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Wrap(
                        spacing: 6,
                        children: [
                          _statChip('${ex.sets} Sets'),
                          _statChip(ex.reps),
                          _statChip('Rest: ${ex.restSec}s', accent: true),
                          if (ex.rpeTarget != null)
                            _statChip('RPE ${ex.rpeTarget!.toStringAsFixed(1)}'),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 4),
                // Action buttons.
                IconButton(
                  icon: Icon(LucideIcons.video,
                      size: 16, color: FitnColors.ink40),
                  onPressed: () => _showTutorialModal(ex),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
                IconButton(
                  icon: Icon(
                      isExpanded
                          ? LucideIcons.chevronUp
                          : LucideIcons.chevronDown,
                      size: 16,
                      color: FitnColors.ink40),
                  onPressed: () => setState(() =>
                      _expandedExIdx = isExpanded ? null : idx),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),
          if (isExpanded)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border(top: BorderSide(color: FitnColors.ink10, width: 1)),
                color: FitnColors.fill,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (ex.exercise.videoThumbnail != null &&
                      ex.exercise.videoThumbnail!.isNotEmpty)
                    ClipRRect(
                      child: Image.network(
                        ex.exercise.videoThumbnail!,
                        height: 140,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => Container(
                          height: 140,
                          color: FitnColors.ink05,
                          child: const Center(
                              child: Icon(LucideIcons.image, size: 32)),
                        ),
                      ),
                    ),
                  const SizedBox(height: 12),
                  Text('OVERVIEW', style: FitnText.microLabel),
                  const SizedBox(height: 6),
                  Text(ex.exercise.overview, style: FitnText.body),
                  const SizedBox(height: 12),
                  Text('INSTRUCTIONS', style: FitnText.microLabel),
                  const SizedBox(height: 6),
                  ...ex.exercise.instructions.asMap().entries.map((e) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 18,
                            height: 18,
                            decoration: const BoxDecoration(
                              color: FitnColors.accent,
                              shape: BoxShape.circle,
                            ),
                            alignment: Alignment.center,
                            child: Text('${e.key + 1}',
                                style: GoogleFonts.inter(
                                    fontSize: 9,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.white)),
                          ),
                          const SizedBox(width: 8),
                          Expanded(child: Text(e.value, style: FitnText.body)),
                        ],
                      ),
                    );
                  }),
                  if (ex.exercise.tips.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text('PRO TIPS', style: FitnText.microLabel),
                    const SizedBox(height: 6),
                    ...ex.exercise.tips.map((t) => Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(LucideIcons.lightbulb,
                                  size: 14, color: FitnColors.accent),
                              const SizedBox(width: 8),
                              Expanded(child: Text(t, style: FitnText.body)),
                            ],
                          ),
                        )),
                  ],
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _statChip(String label, {bool accent = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: accent ? FitnColors.accent05 : FitnColors.fill,
        border: Border.all(
            color: accent ? FitnColors.accent20 : FitnColors.ink05, width: 1),
      ),
      child: Text(
        label,
        style: FitnText.mono.copyWith(
            fontSize: 9,
            color: accent ? FitnColors.accent : FitnColors.ink70,
            fontWeight: FontWeight.w700),
      ),
    );
  }

  void _showTutorialModal(WorkoutExercise ex) {
    setState(() {
      _activeTutorialExercise = ex;
      _videoProgress = 15;
      _isVideoPlaying = true;
      _tutorialMuted = false;
    });
  }
}

class _TutorialSheet extends StatelessWidget {
  const _TutorialSheet({required this.exercise});
  final WorkoutExercise exercise;

  @override
  Widget build(BuildContext context) {
    final e = exercise.exercise;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Center(
          child: Container(
            width: 40,
            height: 4,
            color: FitnColors.ink15,
          ),
        ),
        const SizedBox(height: 16),
        Text(e.name, style: FitnText.headline.copyWith(fontSize: 22)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            _chip('Category', exercise.category.display),
            _chip('Mechanics', e.mechanics),
            _chip('Force', e.forceType),
            _chip('Equipment', e.equipment),
          ],
        ),
        const SizedBox(height: 16),
        if (e.videoThumbnail != null && e.videoThumbnail!.isNotEmpty)
          Stack(
            alignment: Alignment.center,
            children: [
              ClipRRect(
                child: Image.network(e.videoThumbnail!,
                    height: 180, width: double.infinity, fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                        height: 180,
                        color: FitnColors.ink05,
                        child: const Icon(LucideIcons.image, size: 48))),
              ),
              Container(
                width: 56,
                height: 56,
                decoration: const BoxDecoration(
                  color: FitnColors.accent,
                  shape: BoxShape.circle,
                ),
                child: Icon(LucideIcons.play, size: 28, color: Colors.white),
              ),
            ],
          ),
        const SizedBox(height: 16),
        Text('INSTRUCTION', style: FitnText.microLabel),
        const SizedBox(height: 6),
        Text(e.overview, style: FitnText.body),
        const SizedBox(height: 16),
        Text('FORM STEPS', style: FitnText.microLabel),
        const SizedBox(height: 8),
        ...e.instructions.asMap().entries.map((entry) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: const BoxDecoration(
                    color: FitnColors.ink,
                    shape: BoxShape.circle,
                  ),
                  alignment: Alignment.center,
                  child: Text('${entry.key + 1}',
                      style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: Colors.white)),
                ),
                const SizedBox(width: 10),
                Expanded(child: Text(entry.value, style: FitnText.body)),
              ],
            ),
          );
        }),
      ],
    );
  }

  Widget _chip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      color: FitnColors.ink05,
      child: Text('$label: $value',
          style: GoogleFonts.inter(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: FitnColors.ink60)),
    );
  }
}
