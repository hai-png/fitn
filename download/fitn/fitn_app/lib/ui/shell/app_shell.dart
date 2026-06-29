/// App shell — Scaffold + IndexedStack + BottomNav. See spec §7.2.
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../theme/app_theme.dart';
import '../tabs/home_tab.dart';
import '../tabs/workouts_tab.dart';
import '../tabs/meals_tab.dart';
import '../tabs/progress_tab.dart';
import '../tabs/profile_tab.dart';

class AppShell extends ConsumerWidget {
  const AppShell({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appAsync = ref.watch(appNotifierProvider);
    final appState = appAsync.valueOrNull;
    final activeTab = appState?.activeTab ?? Tab.home;

    return Scaffold(
      body: IndexedStack(
        index: Tab.values.indexOf(activeTab),
        children: const [
          HomeTab(),
          WorkoutsTab(),
          MealsTab(),
          ProgressTab(),
          ProfileTab(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: Tab.values.indexOf(activeTab),
        onTap: (i) {
          ref.read(appNotifierProvider.notifier).setActiveTab(Tab.values[i]);
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(LucideIcons.home), label: 'Home'),
          BottomNavigationBarItem(
              icon: Icon(LucideIcons.dumbbell), label: 'Workouts'),
          BottomNavigationBarItem(
              icon: Icon(LucideIcons.utensils), label: 'Meals'),
          BottomNavigationBarItem(
              icon: Icon(LucideIcons.trendingUp), label: 'Progress'),
          BottomNavigationBarItem(
              icon: Icon(LucideIcons.user), label: 'Profile'),
        ],
        selectedIconTheme: const IconThemeData(
          color: AppColors.primary,
          size: 26,
        ),
        unselectedIconTheme: const IconThemeData(
          color: AppColors.textSecondaryDark,
          size: 22,
        ),
      ),
    );
  }
}
