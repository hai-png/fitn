/// Meals tab — 7-day meal rotation. See spec §7.6.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class MealsTab extends ConsumerStatefulWidget {
  const MealsTab({super.key});

  @override
  ConsumerState<MealsTab> createState() => _MealsTabState();
}

class _MealsTabState extends ConsumerState<MealsTab> {
  int _selectedDay = DateTime.now().weekday;

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final plan = appState?.activePlan;

    if (plan == null) {
      return const Center(child: Text('No plan yet.'));
    }

    final meal = plan.meal;
    final day = meal.days[_selectedDay - 1];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Meals'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildHeader(meal),
            const SizedBox(height: 16),
            _buildDayPicker(meal.days),
            const SizedBox(height: 16),
            _buildDaySummary(day),
            const SizedBox(height: 16),
            ...day.meals.map((m) => _MealCard(meal: m)),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(MealPlan meal) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('${meal.mealFrequency} meals/day · 7-day rotation',
            style: const TextStyle(
                fontSize: 20, fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        Text(
          'Cuisine mix: ${meal.cuisineMix.entries.map((e) => "${e.key} (${e.value})").join(", ")}',
          style: const TextStyle(color: AppColors.textSecondaryDark, fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildDayPicker(List<DayPlan> days) {
    return SizedBox(
      height: 64,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: days.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final day = days[i];
          final isSelected = day.dayNumber == _selectedDay;
          final isToday = day.dayNumber == DateTime.now().weekday;
          return GestureDetector(
            onTap: () => setState(() => _selectedDay = day.dayNumber),
            child: Container(
              width: 56,
              decoration: BoxDecoration(
                color: isSelected
                    ? AppColors.primary
                    : AppColors.bgDarkSurface,
                borderRadius: BorderRadius.circular(12),
                border: isToday && !isSelected
                    ? Border.all(color: AppColors.primary, width: 1.5)
                    : null,
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    _dayShort(day.dayNumber),
                    style: TextStyle(
                      fontSize: 11,
                      color: isSelected
                          ? Colors.white
                          : AppColors.textSecondaryDark,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${day.dayNumber}',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: isSelected
                          ? Colors.white
                          : AppColors.textPrimaryDark,
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildDaySummary(DayPlan day) {
    final targetKcal = ref
            .read(appNotifierProvider)
            .valueOrNull
            ?.activePlan
            ?.nutrition
            .calories
            .targetCaloriesKcal ??
        day.totalKcal;
    final delta = day.totalKcal - targetKcal;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                AnimatedNumber(
                  value: day.totalKcal,
                  style: const TextStyle(
                      fontSize: 32, fontWeight: FontWeight.w700),
                ),
                const Text(' kcal',
                    style: TextStyle(color: AppColors.textSecondaryDark)),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: delta.abs() < 100
                        ? AppColors.success.withValues(alpha: 0.15)
                        : AppColors.warning.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '${delta > 0 ? '+' : ''}${delta.round()} kcal',
                    style: TextStyle(
                      color: delta.abs() < 100
                          ? AppColors.success
                          : AppColors.warning,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                MacroRing(
                  label: 'Protein',
                  current: day.totalProteinG,
                  target: ref
                          .read(appNotifierProvider)
                          .valueOrNull
                          ?.activePlan
                          ?.nutrition
                          .macros
                          .proteinG ??
                      day.totalProteinG,
                  unit: 'g',
                  color: AppColors.proteinRing,
                ),
                MacroRing(
                  label: 'Carbs',
                  current: day.totalCarbG,
                  target: ref
                          .read(appNotifierProvider)
                          .valueOrNull
                          ?.activePlan
                          ?.nutrition
                          .macros
                          .carbG ??
                      day.totalCarbG,
                  unit: 'g',
                  color: AppColors.carbRing,
                ),
                MacroRing(
                  label: 'Fat',
                  current: day.totalFatG,
                  target: ref
                          .read(appNotifierProvider)
                          .valueOrNull
                          ?.activePlan
                          ?.nutrition
                          .macros
                          .fatG ??
                      day.totalFatG,
                  unit: 'g',
                  color: AppColors.fatRing,
                ),
                MacroRing(
                  label: 'Fiber',
                  current: day.totalFiberG,
                  target: ref
                          .read(appNotifierProvider)
                          .valueOrNull
                          ?.activePlan
                          ?.nutrition
                          .micronutrients
                          .fiberG ??
                      day.totalFiberG,
                  unit: 'g',
                  color: AppColors.fiberRing,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _dayShort(int n) {
    return switch (n) {
      1 => 'MON',
      2 => 'TUE',
      3 => 'WED',
      4 => 'THU',
      5 => 'FRI',
      6 => 'SAT',
      7 => 'SUN',
      _ => '',
    };
  }
}

class _MealCard extends StatefulWidget {
  const _MealCard({required this.meal});
  final Meal meal;

  @override
  State<_MealCard> createState() => _MealCardState();
}

class _MealCardState extends State<_MealCard> {
  bool _expanded = false;
  bool _logged = false;

  @override
  Widget build(BuildContext context) {
    final m = widget.meal;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        children: [
          ListTile(
            leading: Text(m.mealType.emoji, style: const TextStyle(fontSize: 24)),
            title: Text(m.name,
                style:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
            subtitle: Text(
                '${m.actualKcal.round()} kcal · ${m.actualProteinG.round()}g protein'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: Icon(
                    _logged ? LucideIcons.check : LucideIcons.plus,
                    color: _logged ? AppColors.success : AppColors.primary,
                  ),
                  onPressed: () {
                    setState(() => _logged = !_logged);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(_logged
                            ? 'Meal logged'
                            : 'Meal un-logged'),
                        duration: const Duration(seconds: 1),
                      ),
                    );
                  },
                ),
                IconButton(
                  icon: Icon(_expanded
                      ? LucideIcons.chevronUp
                      : LucideIcons.chevronDown),
                  onPressed: () => setState(() => _expanded = !_expanded),
                ),
              ],
            ),
            onTap: () => setState(() => _expanded = !_expanded),
          ),
          if (_expanded)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (m.recipe != null) ...[
                    Row(
                      children: [
                        _NutriCell('Kcal', m.actualKcal.round().toString()),
                        _NutriCell(
                            'P', '${m.actualProteinG.round()}g'),
                        _NutriCell(
                            'C', '${m.actualCarbG.round()}g'),
                        _NutriCell(
                            'F', '${m.actualFatG.round()}g'),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                        'Recipe: ${m.recipe!.name} (×${m.scaleFactor.toStringAsFixed(2)})',
                        style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textSecondaryDark)),
                    const SizedBox(height: 8),
                    const Text('Ingredients',
                        style: TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    ...m.recipe!.ingredients.map((i) => Padding(
                          padding: const EdgeInsets.only(bottom: 2),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('• ',
                                  style: TextStyle(
                                      color: AppColors.primary)),
                              Expanded(child: Text(i, style: const TextStyle(fontSize: 12))),
                            ],
                          ),
                        )),
                    if (m.foods.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      const Text('Fillers',
                          style: TextStyle(
                              fontSize: 13, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 4),
                      ...m.foods.map((f) => Padding(
                            padding: const EdgeInsets.only(bottom: 2),
                            child: Row(
                              children: [
                                Text('${f.grams.round()}g',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                        fontSize: 12)),
                                const SizedBox(width: 8),
                                Expanded(
                                    child: Text(f.food.name,
                                        style: const TextStyle(fontSize: 12))),
                                Text('${f.kcal.round()} kcal',
                                    style: const TextStyle(
                                        color: AppColors.textSecondaryDark,
                                        fontSize: 11)),
                              ],
                            ),
                          )),
                    ],
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.bgDarkSurface,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(m.selectionReason,
                          style: const TextStyle(
                              fontSize: 11,
                              color: AppColors.textSecondaryDark))),
                  ] else
                    const Text('No recipe matched for this slot.',
                        style: TextStyle(
                            color: AppColors.textSecondaryDark,
                            fontSize: 12)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _NutriCell extends StatelessWidget {
  const _NutriCell(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        margin: const EdgeInsets.symmetric(horizontal: 2),
        decoration: BoxDecoration(
          color: AppColors.bgDarkSurface,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(value,
                style: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.w600)),
            Text(label,
                style: const TextStyle(
                    color: AppColors.textSecondaryDark, fontSize: 10)),
          ],
        ),
      ),
    );
  }
}
