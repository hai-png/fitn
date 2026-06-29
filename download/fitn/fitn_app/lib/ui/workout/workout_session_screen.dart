/// Workout session screen. See spec §7.5.
library;

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../data/isar/collections/collections.dart';
import '../../state/app_state.dart';
import '../../theme/app_theme.dart';

class WorkoutSessionScreen extends ConsumerStatefulWidget {
  const WorkoutSessionScreen({super.key});

  @override
  ConsumerState<WorkoutSessionScreen> createState() =>
      _WorkoutSessionScreenState();
}

class _WorkoutSessionScreenState extends ConsumerState<WorkoutSessionScreen> {
  Timer? _tick;
  int _elapsedSec = 0;
  int _restRemaining = 0;
  DateTime? _restEndsAt;

  @override
  void initState() {
    super.initState();
    _tick = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        _elapsedSec++;
        if (_restEndsAt != null) {
          _restRemaining = _restEndsAt!.difference(DateTime.now()).inSeconds;
          if (_restRemaining <= 0) {
            _restRemaining = 0;
            _restEndsAt = null;
          }
        }
      });
    });
  }

  @override
  void dispose() {
    _tick?.cancel();
    super.dispose();
  }

  void _startRest(int seconds) {
    setState(() {
      _restEndsAt = DateTime.now().add(Duration(seconds: seconds));
      _restRemaining = seconds;
    });
  }

  void _adjustRest(int deltaSec) {
    if (_restEndsAt == null) return;
    setState(() {
      _restEndsAt = _restEndsAt!.add(Duration(seconds: deltaSec));
      _restRemaining = _restEndsAt!.difference(DateTime.now()).inSeconds;
    });
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(workoutSessionProvider);
    if (!session.isActive) {
      return Scaffold(
        appBar: AppBar(title: const Text('No active workout')),
        body: const Center(child: Text('Start a workout from the Workouts tab.')),
      );
    }

    final mins = _elapsedSec ~/ 60;
    final secs = _elapsedSec % 60;

    return Scaffold(
      appBar: AppBar(
        title: Text(session.workoutName ?? 'Workout'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Text('${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w600)),
            ),
          ),
          TextButton(
            onPressed: () => _confirmFinish(),
            child: const Text('Finish'),
          ),
        ],
      ),
      body: SafeArea(
        child: Stack(
          children: [
            ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: session.sets.length,
              itemBuilder: (context, i) {
                final s = session.sets[i];
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: Checkbox(
                      value: s.done,
                      onChanged: (_) {
                        ref.read(workoutSessionProvider.notifier).toggleSet(i);
                        if (!s.done) {
                          // Start rest timer when set is marked done.
                          _startRest(90);
                        }
                      },
                    ),
                    title: Text('Set ${s.setNum} · ${s.exerciseSlug}'),
                    subtitle: Text(
                        '${s.weightKg?.toStringAsFixed(1) ?? "—"}kg × ${s.reps ?? "—"} reps · RPE ${s.rpe?.toStringAsFixed(1) ?? "—"}'),
                    trailing: IconButton(
                      icon: const Icon(LucideIcons.edit),
                      onPressed: () {
                        // Edit set details.
                      },
                    ),
                  ),
                );
              },
            ),
            if (_restEndsAt != null)
              Positioned(
                left: 16,
                right: 16,
                bottom: 16,
                child: _RestTimerBar(
                  remaining: _restRemaining,
                  onAdjust: _adjustRest,
                  onReset: () => _startRest(90),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmFinish() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Finish workout?'),
          content: const Text('Your sets will be saved to your workout history.'),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancel')),
            ElevatedButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Finish')),
          ],
        );
      },
    );
    if (confirmed == true) {
      await ref.read(workoutSessionProvider.notifier).finish();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Workout saved!')),
        );
        Navigator.of(context).pop();
      }
    }
  }
}

class _RestTimerBar extends StatelessWidget {
  const _RestTimerBar({
    required this.remaining,
    required this.onAdjust,
    required this.onReset,
  });

  final int remaining;
  final void Function(int deltaSec) onAdjust;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    final mins = remaining ~/ 60;
    final secs = remaining % 60;
    final isLow = remaining <= 10;
    return Card(
      color: isLow ? AppColors.danger : AppColors.bgDarkElevated,
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(
              color: isLow ? AppColors.danger : AppColors.primary, width: 2)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Icon(isLow ? LucideIcons.zap : LucideIcons.timer,
                color: isLow ? Colors.white : AppColors.primary),
            const SizedBox(width: 8),
            Text(
              isLow ? 'GO!' : 'Rest',
              style: TextStyle(
                color: isLow ? Colors.white : AppColors.textSecondaryDark,
                fontSize: 12,
              ),
            ),
            const Spacer(),
            Text(
              '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: isLow ? Colors.white : AppColors.textPrimaryDark,
              ),
            ),
            const Spacer(),
            IconButton(
              icon: const Icon(LucideIcons.minus),
              iconSize: 18,
              onPressed: () => onAdjust(-15),
            ),
            IconButton(
              icon: const Icon(LucideIcons.rotateCcw),
              iconSize: 18,
              onPressed: onReset,
            ),
            IconButton(
              icon: const Icon(LucideIcons.plus),
              iconSize: 18,
              onPressed: () => onAdjust(15),
            ),
          ],
        ),
      ),
    );
  }
}
