/// Profile tab — Coaching HQ matching FitLife Hub design.
///
/// Features:
/// - User bio card with avatar + metrics grid + allergen warning.
/// - Nutrition blueprint with macro visualizer bars.
/// - Nutritional guidelines list.
/// - Ideal meal schedule suggestions.
/// - Paid orders history.
/// - Reset assessment button.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class ProfileTab extends ConsumerWidget {
  const ProfileTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final profile = appState?.profile;
    final plan = appState?.activePlan;
    final userName = appState?.userName ?? 'Athlete';
    final orders = appState?.orders ?? const [];
    final auth = appState?.auth;

    if (profile == null) {
      return const Center(child: Text('No profile yet.'));
    }

    final macros = plan?.nutrition.macros;
    final totalMacrosGrams = (macros?.proteinG ?? 0) +
        (macros?.carbG ?? 0) +
        (macros?.fatG ?? 0);
    final pPct = totalMacrosGrams > 0
        ? ((macros?.proteinG ?? 0) / totalMacrosGrams * 100).round()
        : 0;
    final cPct = totalMacrosGrams > 0
        ? ((macros?.carbG ?? 0) / totalMacrosGrams * 100).round()
        : 0;
    final fPct = 100 - pPct - cPct;
    final allergens = appState?.preferences?.allergensToAvoid ?? const [];

    return Scaffold(
      backgroundColor: FitnColors.cream,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
          children: [
            // Title.
            FitnSectionLabel('05 — Coaching HQ'),
            Text('Coaching HQ & Profile',
                style: FitnText.headline.copyWith(fontSize: 28)),
            const SizedBox(height: 20),
            // User bio card.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: FitnColors.accent05,
                          border: Border.all(color: FitnColors.accent10, width: 1),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(LucideIcons.user,
                            size: 24, color: FitnColors.accent),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(userName.toUpperCase(),
                                style: GoogleFonts.inter(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                    color: FitnColors.ink)),
                            const SizedBox(height: 2),
                            Text(
                              'Goal: ${profile.primaryGoal.display}',
                              style: FitnText.monoSmall.copyWith(
                                  fontSize: 10, color: FitnColors.ink60),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Metrics grid.
                  Row(
                    children: [
                      Expanded(
                        child: _metricCell(
                            'AGE', '${profile.age} yrs'),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: _metricCell(
                            'WEIGHT', '${profile.weightKg.toStringAsFixed(1)} kg'),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: _metricCell(
                            'HEIGHT', '${profile.heightCm.toStringAsFixed(0)} cm'),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: _metricCell(
                            'DIET', profile.dietType.display,
                            accent: true),
                      ),
                    ],
                  ),
                  if (allergens.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: FitnColors.accent05,
                        border: Border.all(color: FitnColors.accent15, width: 1),
                      ),
                      child: Row(
                        children: [
                          Icon(LucideIcons.alertTriangle,
                              size: 14, color: FitnColors.accent),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Allergen Warning: Sensitive to ${allergens.join(", ")}',
                              style: FitnText.serifItalic.copyWith(fontSize: 10),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),
            // Nutrition blueprint.
            if (plan != null)
              FitnCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(LucideIcons.pieChart, size: 14, color: FitnColors.accent),
                        const SizedBox(width: 6),
                        Text('NUTRITIONAL BLUEPRINT TARGET',
                            style: FitnText.microLabel),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: FitnColors.fill,
                        border: Border.all(color: FitnColors.ink05, width: 1),
                      ),
                      child: Column(
                        children: [
                          Text('SUGGESTED DAILY INTAKE',
                              style: GoogleFonts.inter(
                                  fontSize: 8,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.0,
                                  color: FitnColors.ink40)),
                          const SizedBox(height: 4),
                          Text(
                            '${plan.nutrition.calories.targetCaloriesKcal.round()} kcal / day',
                            style: FitnText.headline.copyWith(fontSize: 22),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    FitnMacroBar(
                      label: 'Protein (Build/Maintain)',
                      value:
                          '${macros?.proteinG.round() ?? 0}g ($pPct%)',
                      percentage: pPct.toDouble(),
                      color: FitnColors.accent,
                    ),
                    const SizedBox(height: 10),
                    FitnMacroBar(
                      label: 'Carbohydrates (Energy)',
                      value: '${macros?.carbG.round() ?? 0}g ($cPct%)',
                      percentage: cPct.toDouble(),
                      color: FitnColors.ink,
                    ),
                    const SizedBox(height: 10),
                    FitnMacroBar(
                      label: 'Fats (Hormonal Health)',
                      value: '${macros?.fatG.round() ?? 0}g ($fPct%)',
                      percentage: fPct.toDouble(),
                      color: FitnColors.ink40,
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 16),
            // Hydration + timeline summary.
            if (plan != null)
              FitnCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(LucideIcons.droplets, size: 14, color: FitnColors.accent),
                        const SizedBox(width: 6),
                        Text('HYDRATION & TIMELINE',
                            style: FitnText.microLabel),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: _metricCell('WATER', '${plan.nutrition.hydration.waterLitersPerDay.toStringAsFixed(1)} L'),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: _metricCell('FIBER', '${plan.nutrition.micronutrients.fiberG.round()} g'),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: _metricCell('WEEKS', '${plan.nutrition.timelineWeeks}'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 16),
            // Orders history.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(LucideIcons.shoppingBag, size: 14, color: FitnColors.accent),
                      const SizedBox(width: 6),
                      Text('PAID ORDERS HISTORY', style: FitnText.microLabel),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (orders.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Center(
                        child: Text(
                            'No completed purchases yet. Preps ordered or gear bought will appear here!',
                            style: FitnText.serifItalic),
                      ),
                    )
                  else
                    ...orders.map((ord) {
                      return Container(
                        padding: const EdgeInsets.all(10),
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: FitnColors.fill,
                          border: Border.all(color: FitnColors.ink05, width: 1),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(ord.id,
                                    style: GoogleFonts.inter(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w700,
                                        color: FitnColors.ink)),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 2),
                                  color: FitnColors.accent,
                                  child: Text(ord.status.toUpperCase(),
                                      style: GoogleFonts.inter(
                                          fontSize: 8,
                                          fontWeight: FontWeight.w700,
                                          letterSpacing: 1.0,
                                          color: Colors.white)),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            ...ord.items.map((item) => Padding(
                                  padding: const EdgeInsets.only(bottom: 2),
                                  child: Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Expanded(
                                        child: Text(
                                          '• ${item.name} (x${item.quantity})',
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: FitnText.serifItalic.copyWith(fontSize: 10),
                                        ),
                                      ),
                                      Text(
                                        '\$${(item.price * item.quantity).toStringAsFixed(2)}',
                                        style: GoogleFonts.inter(
                                            fontSize: 10,
                                            fontWeight: FontWeight.w700,
                                            color: FitnColors.ink),
                                      ),
                                    ],
                                  ),
                                )),
                            const Divider(),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(ord.date,
                                    style: FitnText.monoSmall.copyWith(fontSize: 9)),
                                Text('Total: \$${ord.total.toStringAsFixed(2)}',
                                    style: GoogleFonts.inter(
                                        fontSize: 10,
                                        fontWeight: FontWeight.w700,
                                        color: FitnColors.ink)),
                              ],
                            ),
                          ],
                        ),
                      );
                    }),
                ],
              ),
            ),
            const SizedBox(height: 16),
            // Plan history.
            if ((appState?.planHistory ?? const []).isNotEmpty)
              FitnCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(LucideIcons.history, size: 14, color: FitnColors.accent),
                        const SizedBox(width: 6),
                        Text('PLAN HISTORY', style: FitnText.microLabel),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ...(appState?.planHistory ?? const []).take(5).map((p) {
                      return ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                            p.isActive ? LucideIcons.check : LucideIcons.history,
                            size: 14,
                            color: p.isActive
                                ? FitnColors.accent
                                : FitnColors.ink40),
                        title: Text(
                            '${p.generatedAt.year}-${p.generatedAt.month.toString().padLeft(2, '0')}-${p.generatedAt.day.toString().padLeft(2, '0')} • v${p.engineVersion}',
                            style: GoogleFonts.inter(fontSize: 11)),
                        trailing: p.isActive
                            ? Text('Active',
                                style: GoogleFonts.inter(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    color: FitnColors.accent))
                            : TextButton(
                                onPressed: () => ref
                                    .read(appNotifierProvider.notifier)
                                    .restorePlan(p.planId),
                                child: Text('RESTORE',
                                    style: GoogleFonts.inter(
                                        fontSize: 10,
                                        fontWeight: FontWeight.w700,
                                        color: FitnColors.accent)),
                              ),
                      );
                    }),
                  ],
                ),
              ),
            const SizedBox(height: 16),
            // Account section.
            FitnCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('ACCOUNT', style: FitnText.microLabel),
                  const SizedBox(height: 12),
                  if (auth?.isAuthenticated ?? false) ...[
                    Text(auth?.email ?? 'Signed in',
                        style: GoogleFonts.inter(
                            fontSize: 12, color: FitnColors.ink)),
                    const SizedBox(height: 8),
                    OutlinedButton.icon(
                      onPressed: () => ref
                          .read(authNotifierProvider.notifier)
                          .signOut(),
                      icon: Icon(LucideIcons.logOut, size: 14),
                      label: Text('SIGN OUT',
                          style: GoogleFonts.inter(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.0)),
                    ),
                  ] else ...[
                    Text('Sign in to sync across devices',
                        style: FitnText.serifItalic),
                    const SizedBox(height: 8),
                    ElevatedButton.icon(
                      onPressed: () => Navigator.of(context).pushNamed('/signin'),
                      icon: Icon(LucideIcons.logIn, size: 14),
                      label: Text('SIGN IN',
                          style: FitnText.buttonLabel),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),
            // Reset onboarding.
            OutlinedButton.icon(
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: Text('Reset Assessment?',
                        style: FitnText.headline.copyWith(fontSize: 18)),
                    content: Text(
                        'Are you sure you want to reset your training split, nutritional targets, and clear active plans? This will return you to the onboarding questionnaire.',
                        style: FitnText.body),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('Cancel')),
                      ElevatedButton(
                        onPressed: () {
                          ref.read(appNotifierProvider.notifier).resetOnboarding();
                          Navigator.pop(context);
                        },
                        style: ElevatedButton.styleFrom(
                            backgroundColor: FitnColors.danger),
                        child: const Text('Reset'),
                      ),
                    ],
                  ),
                );
              },
              icon: Icon(LucideIcons.refreshCw, size: 14, color: FitnColors.danger),
              label: Text('RESET ASSESSMENT QUESTIONNAIRE',
                  style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.0,
                      color: FitnColors.danger)),
            ),
            const SizedBox(height: 24),
            Center(
              child: Text(
                'Engine v3.2.0 · Deterministic\nAll data stays on your device',
                textAlign: TextAlign.center,
                style: FitnText.monoSmall.copyWith(fontSize: 9),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricCell(String label, String value, {bool accent = false}) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: FitnColors.fill,
        border: Border.all(color: FitnColors.ink05, width: 1),
      ),
      child: Column(
        children: [
          Text(label,
              style: GoogleFonts.inter(
                  fontSize: 8,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                  color: FitnColors.ink40)),
          const SizedBox(height: 4),
          Text(
            value,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.inter(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: accent ? FitnColors.accent : FitnColors.ink),
          ),
        ],
      ),
    );
  }
}
