/// Top-level MaterialApp.router — uses the Fitn design system.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'data/prefs/app_state_provider.dart';
import 'router.dart';
import 'ui/theme/fitn_design.dart';

class FitnApp extends ConsumerWidget {
  const FitnApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: 'Fitn — FitLife Hub',
      debugShowCheckedModeBanner: false,
      theme: FitnTheme.light(),
      darkTheme: FitnTheme.light(), // light-first design
      themeMode: themeMode,
      routerConfig: router,
    );
  }
}
