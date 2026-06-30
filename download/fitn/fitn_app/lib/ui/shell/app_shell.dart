/// App shell — phone mockup frame + IndexedStack + BottomNav.
/// Matches FitLife Hub's design: 5 tabs (Training, Meals Prep, Logs, Store, Profile).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';
import '../tabs/training_tab.dart';
import '../tabs/meals_tab.dart';
import '../tabs/progress_tab.dart';
import '../tabs/marketplace_tab.dart';
import '../tabs/profile_tab.dart';

class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key});

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  String _timeStr = '';

  @override
  void initState() {
    super.initState();
    _updateTime();
    Stream.periodic(const Duration(seconds: 10)).listen((_) => _updateTime());
  }

  void _updateTime() {
    final now = DateTime.now();
    var h = now.hour;
    final m = now.minute.toString().padLeft(2, '0');
    final ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12;
    if (h == 0) h = 12;
    setState(() => _timeStr = '$h:$m $ampm');
  }

  @override
  Widget build(BuildContext context) {
    final appAsync = ref.watch(appNotifierProvider);
    final appState = appAsync.valueOrNull;
    final activeTab = appState?.activeTab ?? FitnTab.training;
    final hasPlan = appState?.hasOnboarded ?? false;

    return Scaffold(
      backgroundColor: FitnColors.warmCream,
      body: Center(
        child: Container(
          // Phone mockup frame.
          width: double.infinity,
          constraints: const BoxConstraints(maxWidth: 410),
          margin: const EdgeInsets.symmetric(vertical: 0),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.ink, width: 0),
          ),
          child: Column(
            children: [
              // Status bar (matches fitness-app).
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 10),
                decoration: BoxDecoration(
                  color: FitnColors.cream,
                  border: Border(
                      bottom: BorderSide(color: FitnColors.ink05, width: 1)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _timeStr.isEmpty ? '09:41' : _timeStr,
                      style: FitnText.monoSmall.copyWith(
                        color: FitnColors.ink60,
                        fontSize: 11,
                      ),
                    ),
                    Row(
                      children: [
                        Icon(LucideIcons.signal,
                            size: 14, color: FitnColors.ink70),
                        const SizedBox(width: 6),
                        Icon(LucideIcons.wifi,
                            size: 14, color: FitnColors.ink70),
                        const SizedBox(width: 6),
                        Icon(LucideIcons.batteryFull,
                            size: 16, color: FitnColors.ink),
                      ],
                    ),
                  ],
                ),
              ),
              // Body — tab content.
              Expanded(
                child: IndexedStack(
                  index: FitnTab.values.indexOf(activeTab),
                  children: const [
                    TrainingTab(),
                    MealsTab(),
                    ProgressTab(),
                    MarketplaceTab(),
                    ProfileTab(),
                  ],
                ),
              ),
              // Bottom tab bar.
              if (hasPlan)
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.95),
                    border: Border(
                        top: BorderSide(color: FitnColors.ink10, width: 1)),
                  ),
                  padding: const EdgeInsets.only(
                      top: 10, bottom: 18, left: 8, right: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _TabButton(
                        tab: FitnTab.training,
                        icon: LucideIcons.dumbbell,
                        label: 'Training',
                        activeTab: activeTab,
                        onTap: (t) => ref
                            .read(appNotifierProvider.notifier)
                            .setActiveTab(t),
                      ),
                      _TabButton(
                        tab: FitnTab.meals,
                        icon: LucideIcons.utensilsCrossed,
                        label: 'Meals Prep',
                        activeTab: activeTab,
                        onTap: (t) => ref
                            .read(appNotifierProvider.notifier)
                            .setActiveTab(t),
                      ),
                      _TabButton(
                        tab: FitnTab.progress,
                        icon: LucideIcons.activity,
                        label: 'Logs',
                        activeTab: activeTab,
                        onTap: (t) => ref
                            .read(appNotifierProvider.notifier)
                            .setActiveTab(t),
                      ),
                      _TabButton(
                        tab: FitnTab.marketplace,
                        icon: LucideIcons.shoppingBag,
                        label: 'Store',
                        activeTab: activeTab,
                        onTap: (t) => ref
                            .read(appNotifierProvider.notifier)
                            .setActiveTab(t),
                      ),
                      _TabButton(
                        tab: FitnTab.profile,
                        icon: LucideIcons.user,
                        label: 'Profile',
                        activeTab: activeTab,
                        onTap: (t) => ref
                            .read(appNotifierProvider.notifier)
                            .setActiveTab(t),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TabButton extends StatelessWidget {
  const _TabButton({
    required this.tab,
    required this.icon,
    required this.label,
    required this.activeTab,
    required this.onTap,
  });

  final FitnTab tab;
  final IconData icon;
  final String label;
  final FitnTab activeTab;
  final void Function(FitnTab) onTap;

  @override
  Widget build(BuildContext context) {
    final isActive = tab == activeTab;
    return GestureDetector(
      onTap: () => onTap(tab),
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 20,
              color: isActive ? FitnColors.accent : FitnColors.ink40,
            )
                .animate(target: isActive ? 1 : 0)
                .scale(
                    begin: const Offset(1, 1),
                    end: const Offset(1.1, 1.1),
                    duration: 200.ms),
            const SizedBox(height: 4),
            Text(
              label.toUpperCase(),
              style: TextStyle(
                fontSize: 9,
                fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
                letterSpacing: 0.8,
                color: isActive ? FitnColors.accent : FitnColors.ink40,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
