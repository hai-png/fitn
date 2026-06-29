/// Exercise library browser — search + browse all exercises.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../engine/engine_provider.dart';
import '../../ui/theme/fitn_design.dart';

class ExerciseLibraryScreen extends ConsumerStatefulWidget {
  const ExerciseLibraryScreen({super.key});

  @override
  ConsumerState<ExerciseLibraryScreen> createState() =>
      _ExerciseLibraryScreenState();
}

class _ExerciseLibraryScreenState extends ConsumerState<ExerciseLibraryScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final engineAsync = ref.watch(engineProvider);

    return Scaffold(
      backgroundColor: FitnColors.cream,
      appBar: AppBar(
        title: const Text('Exercise Library'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(60),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Search 1,217 exercises...',
                prefixIcon: Icon(LucideIcons.search),
                isDense: true,
              ),
              onChanged: (v) => setState(() => _query = v),
            ),
          ),
        ),
      ),
      body: engineAsync.when(
        loading: () =>
            const Center(child: CircularProgressIndicator(color: FitnColors.accent)),
        error: (e, _) => Center(child: Text('Engine load failed: $e')),
        data: (engine) {
          return FutureBuilder<List<Exercise>>(
            future: _searchExercises(),
            builder: (context, snap) {
              if (!snap.hasData) {
                return const Center(child: CircularProgressIndicator());
              }
              return ListView.builder(
                itemCount: snap.data!.length,
                itemBuilder: (context, i) {
                  final e = snap.data![i];
                  return ListTile(
                    leading: ClipRRect(
                      child: e.videoThumbnail != null &&
                              e.videoThumbnail!.isNotEmpty
                          ? Image.network(e.videoThumbnail!,
                              width: 48, height: 48, fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => Container(
                                  width: 48,
                                  height: 48,
                                  color: FitnColors.ink05,
                                  child: const Icon(LucideIcons.dumbbell)))
                          : Container(
                              width: 48,
                              height: 48,
                              color: FitnColors.ink05,
                              child: const Icon(LucideIcons.dumbbell),
                            ),
                    ),
                    title: Text(e.name,
                        style: GoogleFonts.inter(
                            fontSize: 12, fontWeight: FontWeight.w700)),
                    subtitle: Text(
                      '${e.equipment} • ${e.mechanics} • ${e.experienceLevel.display}',
                      style: GoogleFonts.inter(
                          color: FitnColors.ink50, fontSize: 10),
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }

  Future<List<Exercise>> _searchExercises() async {
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
    return exercises;
  }
}
