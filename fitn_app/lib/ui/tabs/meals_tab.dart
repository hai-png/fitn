/// Meals tab — meal delivery ordering system matching FitLife Hub design.
///
/// Features:
/// - Target macros alignment bar.
/// - Day/meals-per-day configurator.
/// - Auto-generated meal plan suggestions (cycling through eligible meals).
/// - Per-meal swap modal.
/// - Cart with subtotal + loyalty discount + delivery fee.
/// - Checkout flow (address + card).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../data/domain_types.dart';
import '../../engine/engine_provider.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class MealsTab extends ConsumerStatefulWidget {
  const MealsTab({super.key});

  @override
  ConsumerState<MealsTab> createState() => _MealsTabState();
}

class _MealsTabState extends ConsumerState<MealsTab> {
  int _numDays = 5;
  int _mealsPerDay = 3;
  int? _expandedDay = 1;
  List<_DayMealPlan> _plan = [];
  _SwapTarget? _swapTarget;
  bool _isCheckoutOpen = false;
  bool _isProcessing = false;
  bool _isOrderSuccess = false;
  final _addressCtrl = TextEditingController();
  final _cardCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _generatePlan());
  }

  void _generatePlan() async {
    final appState = ref.read(appNotifierProvider).valueOrNull;
    final diet = _mapDiet(appState?.profile?.dietType ?? DietType.omnivore);
    final allergies =
        (appState?.preferences?.allergensToAvoid ?? const []).join(',').toLowerCase();

    // Load recipes from the engine's recipe database (~225 recipes).
    final allRecipes = await ref.read(engineMealRecipesProvider.future);
    final eligible = _eligibleMeals(allRecipes, diet, allergies);

    final slots = _mealsPerDay == 3
        ? ['Breakfast', 'Lunch', 'Dinner']
        : ['Lunch', 'Dinner'];
    final plan = <_DayMealPlan>[];
    for (var d = 1; d <= _numDays; d++) {
      final dayMeals = <_SlotMeal>[];
      for (var s = 0; s < slots.length; s++) {
        final idx = (d * 5 + s * 3) % eligible.length;
        dayMeals.add(_SlotMeal(slot: slots[s], meal: eligible[idx]));
      }
      plan.add(_DayMealPlan(dayNumber: d, meals: dayMeals));
    }
    setState(() => _plan = plan);
  }

  String _mapDiet(DietType d) => switch (d) {
        DietType.vegan => 'vegan',
        DietType.vegetarian => 'vegetarian',
        DietType.omnivore => 'anything',
      };

  /// Filter the engine's recipe database by diet type and allergens.
  List<MealProduct> _eligibleMeals(
      List<MealProduct> allRecipes, String diet, String allergies) {
    var filtered = allRecipes.where((m) {
      if (diet == 'vegan') return m.category == 'vegan';
      if (diet == 'vegetarian') {
        return m.category == 'vegetarian' || m.category == 'vegan';
      }
      return true;
    }).toList();
    if (allergies.isNotEmpty) {
      final allergens = allergies
          .split(',')
          .map((a) => a.trim())
          .where((a) => a.isNotEmpty)
          .toList();
      final safe = filtered.where((m) {
        return !allergens.any((a) =>
            m.name.toLowerCase().contains(a) ||
            m.description.toLowerCase().contains(a));
      }).toList();
      if (safe.isNotEmpty) filtered = safe;
    }
    return filtered.isEmpty ? allRecipes : filtered;
  }

  void _swapMeal(MealProduct replacement) {
    if (_swapTarget == null) return;
    final plan = List<_DayMealPlan>.from(_plan);
    final day = plan[_swapTarget!.dayIndex];
    day.meals[_swapTarget!.mealIndex] =
        _SlotMeal(slot: day.meals[_swapTarget!.mealIndex].slot, meal: replacement);
    setState(() {
      _plan = plan;
      _swapTarget = null;
    });
  }

  void _checkout() {
    setState(() => _isCheckoutOpen = true);
    final name = ref.read(appNotifierProvider).valueOrNull?.userName;
    if (name != null && name.isNotEmpty) {
      _cardCtrl.text = name;
    }
  }

  void _placeOrder() {
    if (_addressCtrl.text.trim().isEmpty || _cardCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please complete delivery address and billing card.')),
      );
      return;
    }
    setState(() => _isProcessing = true);
    Future.delayed(const Duration(seconds: 2), () {
      final totalMeals = _plan.fold(0, (s, d) => s + d.meals.length);
      final basePrice = 13.49;
      final rawSubtotal = totalMeals * basePrice;
      final discountPct = _numDays >= 14 ? 0.18 : _numDays >= 7 ? 0.12 : _numDays >= 5 ? 0.08 : 0.05;
      final discount = rawSubtotal * discountPct;
      final delivery = rawSubtotal > 100 ? 0.0 : 4.99;
      final finalPrice = rawSubtotal - discount + delivery;
      final order = Order(
        id: 'ord-plan-${DateTime.now().millisecondsSinceEpoch}',
        items: [
          CartItem(
            id: 'meal-plan-$_numDays-days',
            name: '$_numDays-Day Delivered Meal Plan ($totalMeals preps)',
            price: finalPrice,
            image: _plan.first.meals.first.meal.image,
            quantity: 1,
            type: 'meal',
          ),
        ],
        total: finalPrice,
        date: DateTime.now().toIso8601String().split('T')[0],
        status: 'processing',
        deliveryAddress: _addressCtrl.text,
      );
      ref.read(appNotifierProvider.notifier).checkout(order);
      setState(() {
        _isProcessing = false;
        _isOrderSuccess = true;
      });
      Future.delayed(const Duration(milliseconds: 3200), () {
        if (mounted) {
          setState(() {
            _isOrderSuccess = false;
            _isCheckoutOpen = false;
            _addressCtrl.clear();
            _cardCtrl.clear();
          });
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final plan = appState?.activePlan;
    final targetCalories = plan?.nutrition.calories.targetCaloriesKcal.round() ?? 2000;
    final totalMeals = _plan.fold(0, (s, d) => s + d.meals.length);
    final totalKcal = _plan.fold(0, (s, d) => s + d.meals.fold(0, (s2, m) => s2 + m.meal.calories));
    final avgDailyKcal = _numDays > 0 ? (totalKcal / _numDays).round() : 0;
    final basePrice = 13.49;
    final rawSubtotal = totalMeals * basePrice;
    final discountPct = _numDays >= 14 ? 0.18 : _numDays >= 7 ? 0.12 : _numDays >= 5 ? 0.08 : 0.05;
    final discount = rawSubtotal * discountPct;
    final delivery = rawSubtotal > 100 ? 0.0 : 4.99;
    final finalPrice = rawSubtotal - discount + delivery;

    return Scaffold(
      backgroundColor: FitnColors.cream,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
              children: [
                // Title header.
                FitnSectionLabel('02 — SMART DELIVERED MEAL PLANS'),
                Text('Custom Nutrition Delivered', style: FitnText.headline.copyWith(fontSize: 28)),
                const SizedBox(height: 6),
                Text(
                  'Calibrated system preps vacuum-sealed fresh, delivered to your door.',
                  style: FitnText.serifItalic,
                ),
                const SizedBox(height: 20),
                // Target macros bar.
                FitnCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(LucideIcons.sparkles, size: 14, color: FitnColors.accent),
                          const SizedBox(width: 6),
                          Text('TARGET CALORIC MATCH RADAR',
                              style: FitnText.microLabel),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _targetCell('YOUR DAILY TARGET', '$targetCalories kcal'),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _targetCell('PLAN DAILY AVERAGE', '$avgDailyKcal kcal',
                                accent: (avgDailyKcal - targetCalories).abs() < 400),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      ClipRRect(
                        child: LinearProgressIndicator(
                          value: targetCalories > 0
                              ? (avgDailyKcal / targetCalories).clamp(0.0, 1.0)
                              : 0,
                          minHeight: 8,
                          color: FitnColors.accent,
                          backgroundColor: FitnColors.fill,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                // Configurator.
                FitnCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('DELIVERY CONFIGURATOR', style: FitnText.microLabel),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Days', style: FitnText.body),
                          Row(
                            children: [
                              _stepBtn(LucideIcons.minus, () => setState(() {
                                if (_numDays > 1) {
                                  _numDays--;
                                  _generatePlan();
                                }
                              })),
                              Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 12),
                                child: Text('$_numDays', style: FitnText.mono.copyWith(fontSize: 16)),
                              ),
                              _stepBtn(LucideIcons.plus, () => setState(() {
                                if (_numDays < 30) {
                                  _numDays++;
                                  _generatePlan();
                                }
                              })),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Meals / Day', style: FitnText.body),
                          Row(
                            children: [
                              _stepBtn(LucideIcons.minus, () => setState(() {
                                if (_mealsPerDay > 2) {
                                  _mealsPerDay--;
                                  _generatePlan();
                                }
                              })),
                              Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 12),
                                child: Text('$_mealsPerDay', style: FitnText.mono.copyWith(fontSize: 16)),
                              ),
                              _stepBtn(LucideIcons.plus, () => setState(() {
                                if (_mealsPerDay < 3) {
                                  _mealsPerDay++;
                                  _generatePlan();
                                }
                              })),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                // Day plans.
                ..._plan.map((d) {
                  final idx = _plan.indexOf(d);
                  final isExpanded = _expandedDay == d.dayNumber;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: FitnCard(
                      child: Column(
                        children: [
                          InkWell(
                            onTap: () => setState(() =>
                                _expandedDay = isExpanded ? null : d.dayNumber),
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Row(
                                children: [
                                  Container(
                                    width: 32,
                                    height: 32,
                                    color: FitnColors.ink,
                                    alignment: Alignment.center,
                                    child: Text('${d.dayNumber}',
                                        style: GoogleFonts.inter(
                                            fontSize: 13,
                                            fontWeight: FontWeight.w700,
                                            color: Colors.white)),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text('DAY ${d.dayNumber}',
                                            style: FitnText.microLabel),
                                        Text(
                                          '${d.meals.length} meals • ${d.meals.fold(0, (s, m) => s + m.meal.calories)} kcal',
                                          style: FitnText.mono.copyWith(fontSize: 11),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Icon(
                                    isExpanded
                                        ? LucideIcons.chevronUp
                                        : LucideIcons.chevronDown,
                                    size: 16,
                                    color: FitnColors.ink40,
                                  ),
                                ],
                              ),
                            ),
                          ),
                          if (isExpanded)
                            Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                children: d.meals.asMap().entries.map((e) {
                                  final mealIdx = e.key;
                                  final sm = e.value;
                                  return Padding(
                                    padding: const EdgeInsets.only(bottom: 8),
                                    child: _mealRow(idx, mealIdx, sm),
                                  );
                                }).toList(),
                              ),
                            ),
                        ],
                      ),
                    ),
                  );
                }),
                const SizedBox(height: 20),
                // Order summary.
                FitnCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('ORDER SUMMARY', style: FitnText.microLabel),
                      const SizedBox(height: 12),
                      _summaryRow('Meals', '$totalMeals preps × \$$basePrice'),
                      _summaryRow('Subtotal', '\$${rawSubtotal.toStringAsFixed(2)}'),
                      _summaryRow(
                          'Multi-day discount (${(discountPct * 100).round()}%)',
                          '-\$${discount.toStringAsFixed(2)}'),
                      _summaryRow('Delivery fee',
                          delivery == 0 ? 'FREE' : '\$${delivery.toStringAsFixed(2)}'),
                      const Divider(),
                      _summaryRow('TOTAL', '\$${finalPrice.toStringAsFixed(2)}',
                          bold: true),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _checkout,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: FitnColors.accent,
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(LucideIcons.creditCard, size: 16, color: Colors.white),
                            const SizedBox(width: 8),
                            Text('PLACE ORDER', style: FitnText.buttonLabel),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            // Swap modal.
            if (_swapTarget != null) _buildSwapModal(),
            // Checkout modal.
            if (_isCheckoutOpen) _buildCheckoutModal(finalPrice),
            // Success overlay.
            if (_isOrderSuccess) _buildSuccessOverlay(),
          ],
        ),
      ),
    );
  }

  Widget _buildSwapModal() {
    final diet = _mapDiet(ref.read(appNotifierProvider).valueOrNull?.profile?.dietType ?? DietType.omnivore);
    final allergies = (ref.read(appNotifierProvider).valueOrNull?.preferences?.allergensToAvoid ?? const []).join(',').toLowerCase();
    // Load eligible recipes from engine asynchronously — use the cached
    // provider value if available, otherwise show a loading state.
    final recipesAsync = ref.watch(engineMealRecipesProvider);
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(20),
          padding: const EdgeInsets.all(16),
          constraints: const BoxConstraints(maxHeight: 500),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.ink, width: 1),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('SWAP MEAL', style: FitnText.microLabel),
                  IconButton(
                    icon: Icon(LucideIcons.x, size: 16),
                    onPressed: () => setState(() => _swapTarget = null),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Expanded(
                child: recipesAsync.when(
                  loading: () => const Center(
                      child: CircularProgressIndicator(
                          color: FitnColors.accent)),
                  error: (e, _) => Center(
                      child: Text('Error loading recipes: $e',
                          style: FitnText.serifItalic)),
                  data: (allRecipes) {
                    final eligible =
                        _eligibleMeals(allRecipes, diet, allergies);
                    return ListView.separated(
                      shrinkWrap: true,
                      itemCount: eligible.length,
                      separatorBuilder: (_, __) =>
                          const SizedBox(height: 8),
                      itemBuilder: (context, idx) {
                        final m = eligible[idx];
                    return InkWell(
                      onTap: () => _swapMeal(m),
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        color: Colors.white,
                        child: Row(
                          children: [
                            ClipRRect(
                              child: Image.network(m.image,
                                  width: 48, height: 48, fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => Container(
                                      width: 48,
                                      height: 48,
                                      color: FitnColors.ink05,
                                      child: Icon(LucideIcons.utensils, size: 18))),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(m.name,
                                      style: GoogleFonts.inter(
                                          fontSize: 11, fontWeight: FontWeight.w700)),
                                  Text('${m.calories} kcal • ${m.protein}g protein',
                                      style: FitnText.monoSmall.copyWith(fontSize: 9)),
                                ],
                              ),
                            ),
                            Text('\$${m.price.toStringAsFixed(2)}',
                                style: FitnText.mono.copyWith(fontSize: 11)),
                          ],
                        ),
                      ),
                    );
                  },
                );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCheckoutModal(double total) {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(20),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.ink, width: 1),
          ),
          child: _isProcessing
              ? Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(color: FitnColors.accent),
                    const SizedBox(height: 16),
                    Text('Processing payment...', style: FitnText.bodyItalic),
                  ],
                )
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('CHECKOUT', style: FitnText.microLabel),
                        IconButton(
                          icon: Icon(LucideIcons.x, size: 16),
                          onPressed: () => setState(() => _isCheckoutOpen = false),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text('Total: \$${total.toStringAsFixed(2)}',
                        style: FitnText.headline.copyWith(fontSize: 22)),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _addressCtrl,
                      decoration: const InputDecoration(labelText: 'Delivery Address'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _cardCtrl,
                      decoration: const InputDecoration(labelText: 'Cardholder Name / Card Number'),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _placeOrder,
                      style: ElevatedButton.styleFrom(backgroundColor: FitnColors.accent),
                      child: Text('PLACE ORDER • \$${total.toStringAsFixed(2)}',
                          style: FitnText.buttonLabel),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildSuccessOverlay() {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(40),
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.accent, width: 2),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(LucideIcons.checkCircle2, size: 56, color: FitnColors.accent),
              const SizedBox(height: 16),
              Text('ORDER PLACED!', style: FitnText.headline.copyWith(fontSize: 20)),
              const SizedBox(height: 8),
              Text('Your meal plan is now being prepared.', style: FitnText.serifItalic),
            ],
          ),
        ),
      ),
    );
  }

  Widget _mealRow(int dayIdx, int mealIdx, _SlotMeal sm) {
    return Container(
      padding: const EdgeInsets.all(8),
      margin: const EdgeInsets.only(bottom: 6),
      color: Colors.white,
      child: Row(
        children: [
          ClipRRect(
            child: Image.network(sm.meal.image,
                width: 56, height: 56, fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(
                    width: 56,
                    height: 56,
                    color: FitnColors.ink05,
                    child: Icon(LucideIcons.utensils, size: 20))),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(sm.slot.toUpperCase(),
                    style: GoogleFonts.inter(
                        fontSize: 8,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.4,
                        color: FitnColors.ink40)),
                const SizedBox(height: 2),
                Text(sm.meal.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.inter(
                        fontSize: 11, fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text('${sm.meal.calories} kcal',
                        style: FitnText.monoSmall.copyWith(fontSize: 9)),
                    const SizedBox(width: 8),
                    Text('${sm.meal.protein}g P',
                        style: FitnText.monoSmall.copyWith(
                            fontSize: 9, color: FitnColors.accent)),
                    const Spacer(),
                    Text('\$${sm.meal.price.toStringAsFixed(2)}',
                        style: FitnText.mono.copyWith(fontSize: 10)),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(LucideIcons.refreshCw, size: 14, color: FitnColors.ink40),
            onPressed: () => setState(() =>
                _swapTarget = _SwapTarget(dayIndex: dayIdx, mealIndex: mealIdx)),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
        ],
      ),
    );
  }

  Widget _targetCell(String label, String value, {bool accent = false}) {
    return Container(
      padding: const EdgeInsets.all(10),
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
            style: FitnText.mono.copyWith(
                fontSize: 13,
                color: accent ? FitnColors.accent : FitnColors.ink,
                fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  Widget _summaryRow(String label, String value, {bool bold = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: bold ? FontWeight.w700 : FontWeight.w400,
                  color: FitnColors.ink70)),
          Text(value,
              style: FitnText.mono.copyWith(
                  fontSize: 11,
                  fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
                  color: bold ? FitnColors.accent : FitnColors.ink)),
        ],
      ),
    );
  }

  Widget _stepBtn(IconData icon, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Container(
        width: 28,
        height: 28,
        decoration: BoxDecoration(
          color: FitnColors.ink,
          shape: BoxShape.circle,
        ),
        child: Icon(icon, size: 14, color: Colors.white),
      ),
    );
  }
}

class _DayMealPlan {
  _DayMealPlan({required this.dayNumber, required this.meals});
  final int dayNumber;
  final List<_SlotMeal> meals;
}

class _SlotMeal {
  _SlotMeal({required this.slot, required this.meal});
  final String slot;
  final MealProduct meal;
}

class _SwapTarget {
  _SwapTarget({required this.dayIndex, required this.mealIndex});
  final int dayIndex;
  final int mealIndex;
}
