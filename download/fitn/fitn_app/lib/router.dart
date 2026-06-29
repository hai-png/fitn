/// go_router config. See spec §6.2.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'state/app_state.dart';
import 'ui/auth/signin_screen.dart';
import 'ui/exercise_library/library_screen.dart';
import 'ui/onboarding/onboarding_screen.dart';
import 'ui/settings/settings_screen.dart';
import 'ui/shell/app_shell.dart';
import 'ui/workout/workout_session_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(path: '/', builder: (_, __) => const AppShell()),
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingScreen()),
      GoRoute(path: '/signin', builder: (_, __) => const SignInScreen()),
      GoRoute(
          path: '/auth/callback',
          builder: (_, __) => const SignInScreen()),
      GoRoute(
          path: '/workout-session',
          builder: (_, __) => const WorkoutSessionScreen()),
      GoRoute(
          path: '/exercise-library',
          builder: (_, __) => const ExerciseLibraryScreen()),
      GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
    ],
    redirect: (context, state) {
      final appAsync = ref.read(appNotifierProvider);
      final appState = appAsync.valueOrNull;
      if (appState == null) return null;
      if (!appState.hasOnboarded &&
          state.path != '/onboarding' &&
          state.path != '/signin' &&
          state.path != '/auth/callback') {
        return '/onboarding';
      }
      return null;
    },
  );
});
