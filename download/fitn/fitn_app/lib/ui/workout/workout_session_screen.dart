/// Workout session screen — full-screen set/rep/weight/RPE logger with rest timer.
library;

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../data/isar/collections/collections.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

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
        backgroundColor: FitnColors.cream,
        appBar: AppBar(title: const Text('No active workout')),
        body: const Center(child: Text('Start a workout from the Training tab.')),
      );
    }

    final mins = _elapsedSec ~/ 60;
    final secs = _elapsedSec % 60;

    return Scaffold(
      backgroundColor: FitnColors.cream,
      appBar: AppBar(
        title: Text(session.workoutName ?? 'Workout'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Text(
                '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}',
                style: FitnText.mono.copyWith(
                    fontSize: 14, fontWeight: FontWeight.w700),
              ),
            ),
          ),
          TextButton(
            onPressed: _confirmFinish,
            child: Text('FINISH',
                style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.0,
                    color: FitnColors.accent)),
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
                        if (!s.done) _startRest(90);
                      },
                    ),
                    title: Text('Set ${s.setNum} • ${s.exerciseSlug}',
                        style: GoogleFonts.inter(
                            fontSize: 13, fontWeight: FontWeight.w700)),
                    subtitle: Text(
                        '${s.weightKg?.toStringAsFixed(1) ?? "—"}kg × ${s.reps ?? "—"} reps • RPE ${s.rpe?.toStringAsFixed(1) ?? "—"}',
                        style: FitnText.monoSmall),
                    trailing: IconButton(
                      icon: Icon(LucideIcons.edit, size: 16),
                      onPressed: () {},
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
      builder: (context) => AlertDialog(
        title: Text('Finish workout?',
            style: FitnText.headline.copyWith(fontSize: 18)),
        content: Text('Your sets will be saved to your workout history.',
            style: FitnText.body),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Finish')),
        ],
      ),
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
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: isLow ? FitnColors.accent : FitnColors.ink,
        border: Border.all(
            color: isLow ? FitnColors.accent : FitnColors.ink, width: 2),
      ),
      child: Row(
        children: [
          Icon(
            isLow ? LucideIcons.zap : LucideIcons.timer,
            color: Colors.white,
            size: 18,
          ),
          const SizedBox(width: 8),
          Text(
            isLow ? 'GO!' : 'Rest',
            style: GoogleFonts.inter(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.0,
                color: Colors.white70),
          ),
          const Spacer(),
          Text(
            '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}',
            style: FitnText.mono.copyWith(
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: Colors.white),
          ),
          const Spacer(),
          IconButton(
            icon: Icon(LucideIcons.minus, color: Colors.white, size: 16),
            onPressed: () => onAdjust(-15),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
          IconButton(
            icon: Icon(LucideIcons.rotateCcw, color: Colors.white, size: 16),
            onPressed: onReset,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
          IconButton(
            icon: Icon(LucideIcons.plus, color: Colors.white, size: 16),
            onPressed: () => onAdjust(15),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
        ],
      ),
    );
  }
}
