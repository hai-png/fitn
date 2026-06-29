/// Exercise library browser. See spec §7.9.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../engine/engine_provider.dart';
import '../../theme/app_theme.dart';

class ExerciseLibraryScreen extends ConsumerStatefulWidget {
  const ExerciseLibraryScreen({super.key});

  @override
  ConsumerState<ExerciseLibraryScreen> createState() =>
      _ExerciseLibraryScreenState();
}

class _ExerciseLibraryScreenState extends ConsumerState<ExerciseLibraryScreen> {
  String _query = '';
  String? _muscleFilter;
  String? _equipmentFilter;
  final _scrollController = ScrollController();

  @override
  Widget build(BuildContext context) {
    final engineAsync = ref.watch(engineProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Exercise Library'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(60),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Search 1,217 exercises…',
                prefixIcon: Icon(LucideIcons.search),
                isDense: true,
              ),
              onChanged: (v) => setState(() => _query = v),
            ),
          ),
        ),
      ),
      body: engineAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Engine load failed: $e')),
        data: (engine) {
          // For simplicity, search the engine's exercises via the public API.
          // We don't have a direct search method on the engine — we re-load.
          return FutureBuilder<List<Exercise>>(
            future: _searchExercises(engine),
            builder: (context, snap) {
              if (!snap.hasData) {
                return const Center(child: CircularProgressIndicator());
              }
              final results = snap.data!;
              return ListView.builder(
                controller: _scrollController,
                itemCount: results.length,
                itemBuilder: (context, i) {
                  final e = results[i];
                  return ListTile(
                    leading: ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: e.videoThumbnail != null &&
                              e.videoThumbnail!.isNotEmpty
                          ? Image.network(e.videoThumbnail!,
                              width: 56, height: 56, fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => Container(
                                  width: 56,
                                  height: 56,
                                  color: AppColors.bgDarkSurface,
                                  child: const Icon(LucideIcons.dumbbell)))
                          : Container(
                              width: 56,
                              height: 56,
                              color: AppColors.bgDarkSurface,
                              child: const Icon(LucideIcons.dumbbell),
                            ),
                    ),
                    title: Text(e.name),
                    subtitle: Text(
                      '${e.equipment} · ${e.mechanics} · ${e.experienceLevel.display}',
                      style: const TextStyle(
                          color: AppColors.textSecondaryDark, fontSize: 11),
                    ),
                    onTap: () {
                      // Show detail sheet (similar to Workouts tab).
                    },
                  );
                },
              );
            },
          );
        },
      ),
    );
  }

  Future<List<Exercise>> _searchExercises(FitnEngine engine) async {
    // Use the engine data — we don't expose search directly via FitnEngine,
    // so we use the loaded data's exercise list.
    final data = await getEngineData();
    var exercises = data.exercises;
    if (_query.isNotEmpty) {
      final q = _query.toLowerCase();
      exercises = exercises
          .where((e) =>
              e.name.toLowerCase().contains(q) ||
              e.slug.toLowerCase().contains(q))
          .toList();
    }
    if (_muscleFilter != null) {
      exercises = exercises
          .where((e) => e.muscleGroups.contains(_muscleFilter!))
          .toList();
    }
    if (_equipmentFilter != null) {
      exercises = exercises
          .where((e) =>
              e.equipment.toLowerCase() == _equipmentFilter!.toLowerCase())
          .toList();
    }
    return exercises;
  }
}
