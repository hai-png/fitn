/// Onboarding — 5-step wizard. See spec §7.1.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  int _step = 0;
  bool _isSubmitting = false;

  // Step 1: Basics.
  final _ageCtrl = TextEditingController(text: '30');
  Sex _sex = Sex.male;
  final _heightCtrl = TextEditingController(text: '180');
  final _weightCtrl = TextEditingController(text: '75');

  // Step 2: Body (optional).
  double? _bodyFatPct;
  final _neckCtrl = TextEditingController();
  final _waistCtrl = TextEditingController();
  final _hipCtrl = TextEditingController();
  bool _bfUnknown = true;

  // Step 3: Activity.
  ActivityLevel _activity = ActivityLevel.lightlyActive;
  TrainingStatus _status = TrainingStatus.novice;
  EquipmentAccess _equipment = EquipmentAccess.fullGym;

  // Step 4: Goal.
  PrimaryGoal _goal = PrimaryGoal.muscleGain;
  int _daysPerWeek = 4;
  TrainingTimeOfDay _timeOfDay = TrainingTimeOfDay.evening;

  // Step 5: Preferences.
  DietType _diet = DietType.omnivore;
  int _mealFreq = 3;
  String? _cuisine;
  final Set<String> _allergens = {};
  final Set<String> _muscleFocus = {};
  bool _includePrePost = true;

  @override
  void dispose() {
    _ageCtrl.dispose();
    _heightCtrl.dispose();
    _weightCtrl.dispose();
    _neckCtrl.dispose();
    _waistCtrl.dispose();
    _hipCtrl.dispose();
    super.dispose();
  }

  bool get _isStepValid {
    switch (_step) {
      case 0:
        return _ageCtrl.text.isNotEmpty &&
            _heightCtrl.text.isNotEmpty &&
            _weightCtrl.text.isNotEmpty &&
            int.tryParse(_ageCtrl.text) != null &&
            int.tryParse(_ageCtrl.text)! >= 18 &&
            int.tryParse(_ageCtrl.text)! <= 100 &&
            double.tryParse(_heightCtrl.text) != null &&
            double.tryParse(_weightCtrl.text) != null;
      case 1:
        return true; // all optional
      case 2:
        return true;
      case 3:
        return true;
      case 4:
        return true;
      default:
        return true;
    }
  }

  Future<void> _submit() async {
    setState(() => _isSubmitting = true);
    try {
      final profile = UserProfile(
        age: int.parse(_ageCtrl.text),
        sex: _sex,
        heightCm: double.parse(_heightCtrl.text),
        weightKg: double.parse(_weightCtrl.text),
        activityLevel: _activity,
        trainingStatus: _status,
        primaryGoal: _goal,
        trainingDaysPerWeek: _daysPerWeek,
        equipmentAccess: _equipment,
        bodyFatPct: _bfUnknown ? null : _bodyFatPct,
        neckCm: _neckCtrl.text.isEmpty ? null : double.tryParse(_neckCtrl.text),
        waistCm:
            _waistCtrl.text.isEmpty ? null : double.tryParse(_waistCtrl.text),
        hipCm: _hipCtrl.text.isEmpty ? null : double.tryParse(_hipCtrl.text),
        trainingTimeOfDay: _timeOfDay,
      );
      final prefs = PlanPreferences(
        dietType: _diet,
        mealFrequency: _mealFreq,
        cuisinePreference: _cuisine,
        allergensToAvoid: _allergens.toList(),
        muscleFocus: _muscleFocus.toList(),
        includePrePostWorkout: _includePrePost,
      );
      await ref.read(appNotifierProvider.notifier).setProfile(profile);
      await ref.read(appNotifierProvider.notifier).setPreferences(prefs);
      await ref.read(appNotifierProvider.notifier).generatePlan();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Your plan is ready!')),
        );
      }
    } on PartialAssessmentError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Assessment incomplete: ${e.message}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to generate plan: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final isGenerating = appState?.planGenerating ?? false;

    return Scaffold(
      appBar: AppBar(
        title: Text(_stepTitle()),
        leading: _step > 0
            ? IconButton(
                icon: const Icon(LucideIcons.arrowLeft),
                onPressed: () => setState(() => _step--),
              )
            : null,
      ),
      body: _isSubmitting || isGenerating
          ? _buildLoading()
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _buildProgressDots(),
                  const SizedBox(height: 24),
                  Expanded(child: _buildStepContent()),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      if (_step > 0)
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => setState(() => _step--),
                            child: const Text('Back'),
                          ),
                        ),
                      if (_step > 0) const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: _isStepValid
                              ? () {
                                  if (_step < 4) {
                                    setState(() => _step++);
                                  } else {
                                    _submit();
                                  }
                                }
                              : null,
                          child: Text(_step < 4 ? 'Continue' : 'Generate Plan'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
    );
  }

  String _stepTitle() {
    return switch (_step) {
      0 => 'Step 1 · Basics',
      1 => 'Step 2 · Body (Optional)',
      2 => 'Step 3 · Activity',
      3 => 'Step 4 · Goal',
      4 => 'Step 5 · Preferences',
      _ => '',
    };
  }

  Widget _buildProgressDots() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(5, (i) {
        final isPast = i < _step;
        final isCurrent = i == _step;
        return GestureDetector(
          onTap: isPast ? () => setState(() => _step = i) : null,
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 4),
            width: isCurrent ? 24 : 8,
            height: 8,
            decoration: BoxDecoration(
              color: isCurrent || isPast
                  ? AppColors.primary
                  : AppColors.bgDarkSurface,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildStepContent() {
    return switch (_step) {
      0 => _buildBasicsStep(),
      1 => _buildBodyStep(),
      2 => _buildActivityStep(),
      3 => _buildGoalStep(),
      4 => _buildPreferencesStep(),
      _ => const SizedBox(),
    };
  }

  Widget _buildLoading() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const ProgressRing(
            progress: 0.7,
            size: 80,
            color: AppColors.primary,
          ).animate(onPlay: (c) => c.repeat()).rotate(duration: 1500.ms),
          const SizedBox(height: 24),
          Text(
            'Generating your plan…',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 32),
          const SkeletonCard(),
          const SizedBox(height: 12),
          const SkeletonCard(),
        ],
      ),
    );
  }

  Widget _buildBasicsStep() {
    return ListView(
      children: [
        TextField(
          controller: _ageCtrl,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Age (18-100)'),
        ),
        const SizedBox(height: 16),
        const Text('Sex', style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _ChoiceChip(
                label: 'Male',
                selected: _sex == Sex.male,
                onTap: () => setState(() => _sex = Sex.male),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _ChoiceChip(
                label: 'Female',
                selected: _sex == Sex.female,
                onTap: () => setState(() => _sex = Sex.female),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _heightCtrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Height (cm, 140-230)'),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _weightCtrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Weight (kg, 35-300)'),
        ),
      ],
    );
  }

  Widget _buildBodyStep() {
    return ListView(
      children: [
        SwitchListTile(
          title: const Text('Body fat % unknown'),
          subtitle: const Text(
              'If unknown, the engine estimates via Navy method or CUN-BAE.'),
          value: _bfUnknown,
          onChanged: (v) => setState(() {
            _bfUnknown = v;
            if (v) _bodyFatPct = null;
          }),
        ),
        if (!_bfUnknown) ...[
          Text('Body Fat %: ${_bodyFatPct?.toStringAsFixed(0) ?? '—'}',
              style: const TextStyle(color: AppColors.textSecondaryDark)),
          Slider(
            value: _bodyFatPct ?? 18,
            min: 2,
            max: 50,
            divisions: 48,
            label: '${(_bodyFatPct ?? 18).round()}%',
            onChanged: (v) => setState(() => _bodyFatPct = v),
          ),
        ],
        const SizedBox(height: 16),
        TextField(
          controller: _neckCtrl,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Neck (cm, optional)'),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _waistCtrl,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Waist (cm, optional)'),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _hipCtrl,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
              labelText: 'Hip (cm, optional — required for females)'),
        ),
      ],
    );
  }

  Widget _buildActivityStep() {
    return ListView(
      children: [
        const Text('Activity Level',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        ...ActivityLevel.values.map((a) => _ChoiceTile(
              label: a.display,
              subtitle: _activityDescription(a),
              selected: _activity == a,
              onTap: () => setState(() => _activity = a),
            )),
        const SizedBox(height: 16),
        const Text('Training Status',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 2.5,
          children: TrainingStatus.values.map((s) {
            return _ChoiceChip(
              label: s.display,
              selected: _status == s,
              onTap: () => setState(() => _status = s),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
        const Text('Equipment Access',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        ...EquipmentAccess.values.map((e) => _ChoiceTile(
              label: '${_equipmentEmoji(e)} ${e.display}',
              subtitle: _equipmentDescription(e),
              selected: _equipment == e,
              onTap: () => setState(() => _equipment = e),
            )),
      ],
    );
  }

  Widget _buildGoalStep() {
    return ListView(
      children: [
        const Text('Primary Goal',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        ...PrimaryGoal.values.map((g) => _ChoiceTile(
              label: '${_goalEmoji(g)} ${g.display}',
              subtitle: _goalDescription(g),
              selected: _goal == g,
              onTap: () => setState(() => _goal = g),
            )),
        const SizedBox(height: 16),
        Text('Training Days per Week: $_daysPerWeek',
            style: const TextStyle(color: AppColors.textSecondaryDark)),
        Slider(
          value: _daysPerWeek.toDouble(),
          min: 2,
          max: 6,
          divisions: 4,
          label: '$_daysPerWeek',
          onChanged: (v) => setState(() => _daysPerWeek = v.round()),
        ),
        const SizedBox(height: 16),
        const Text('Time of Day',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        Row(
          children: TrainingTimeOfDay.values.map((t) {
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.only(right: 8),
                child: _ChoiceChip(
                  label: '${_timeOfDayEmoji(t)} ${t.display}',
                  selected: _timeOfDay == t,
                  onTap: () => setState(() => _timeOfDay = t),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildPreferencesStep() {
    return ListView(
      children: [
        const Text('Diet Type',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        Row(
          children: DietType.values.map((d) {
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.only(right: 8),
                child: _ChoiceChip(
                  label: d.display,
                  selected: _diet == d,
                  onTap: () => setState(() => _diet = d),
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
        Text('Meal Frequency: $_mealFreq meals/day',
            style: const TextStyle(color: AppColors.textSecondaryDark)),
        Slider(
          value: _mealFreq.toDouble(),
          min: 2,
          max: 5,
          divisions: 3,
          label: '$_mealFreq',
          onChanged: (v) => setState(() => _mealFreq = v.round()),
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          value: _cuisine,
          decoration: const InputDecoration(labelText: 'Cuisine Preference'),
          items: const [
            DropdownMenuItem(value: null, child: Text('Any')),
            DropdownMenuItem(value: 'american', child: Text('American')),
            DropdownMenuItem(value: 'ethiopian', child: Text('Ethiopian')),
            DropdownMenuItem(value: 'italian', child: Text('Italian')),
            DropdownMenuItem(value: 'mexican', child: Text('Mexican')),
            DropdownMenuItem(value: 'asian', child: Text('Asian')),
            DropdownMenuItem(
                value: 'mediterranean', child: Text('Mediterranean')),
          ],
          onChanged: (v) => setState(() => _cuisine = v),
        ),
        const SizedBox(height: 16),
        const Text('Allergens to Avoid',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            'dairy',
            'gluten',
            'eggs',
            'soy',
            'peanuts',
            'tree_nuts',
            'shellfish',
            'fish',
            'sesame',
            'corn'
          ].map((a) {
            return FilterChip(
              label: Text(a),
              selected: _allergens.contains(a),
              onSelected: (sel) {
                setState(() {
                  if (sel) {
                    _allergens.add(a);
                  } else {
                    _allergens.remove(a);
                  }
                });
              },
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
        const Text('Muscle Focus',
            style: TextStyle(color: AppColors.textSecondaryDark)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            'chest',
            'back',
            'shoulders',
            'arms',
            'legs',
            'glutes',
            'core',
            'calves'
          ].map((m) {
            return FilterChip(
              label: Text(m),
              selected: _muscleFocus.contains(m),
              onSelected: (sel) {
                setState(() {
                  if (sel) {
                    _muscleFocus.add(m);
                  } else {
                    _muscleFocus.remove(m);
                  }
                });
              },
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
        SwitchListTile(
          title: const Text('Include pre/post workout meals'),
          value: _includePrePost,
          onChanged: (v) => setState(() => _includePrePost = v),
        ),
      ],
    );
  }

  String _activityDescription(ActivityLevel a) {
    return switch (a) {
      ActivityLevel.sedentary => 'Little to no exercise, desk job.',
      ActivityLevel.mostlySedentary => 'Daily light activity, office work.',
      ActivityLevel.lightlyActive => '1-3 workouts/week or daily walks.',
      ActivityLevel.active => '4-5 workouts/week or active job.',
      ActivityLevel.highlyActive => '6-7 workouts/week or heavy labor.',
    };
  }

  String _equipmentDescription(EquipmentAccess e) {
    return switch (e) {
      EquipmentAccess.fullGym => 'Gym membership — full equipment (33 types).',
      EquipmentAccess.homeGym =>
        'Home setup — barbell, dumbbells, kettlebells (9 types).',
      EquipmentAccess.bodyweightOnly => 'Bodyweight + bands only (2 types).',
    };
  }

  String _goalDescription(PrimaryGoal g) {
    return switch (g) {
      PrimaryGoal.fatLoss => 'Prioritise fat loss with a calorie deficit.',
      PrimaryGoal.muscleGain => 'Build muscle with a calorie surplus.',
      PrimaryGoal.recomp => 'Lose fat + build muscle simultaneously.',
      PrimaryGoal.maintenance => 'Maintain current physique.',
      PrimaryGoal.strength => 'Build strength with progressive overload.',
    };
  }

  String _equipmentEmoji(EquipmentAccess e) {
    return switch (e) {
      EquipmentAccess.fullGym => '🏟️',
      EquipmentAccess.homeGym => '🏠',
      EquipmentAccess.bodyweightOnly => '🤸',
    };
  }

  String _goalEmoji(PrimaryGoal g) {
    return switch (g) {
      PrimaryGoal.fatLoss => '🔥',
      PrimaryGoal.muscleGain => '💪',
      PrimaryGoal.recomp => '⚖️',
      PrimaryGoal.maintenance => '🎯',
      PrimaryGoal.strength => '🏋️',
    };
  }

  String _timeOfDayEmoji(TrainingTimeOfDay t) {
    return switch (t) {
      TrainingTimeOfDay.morning => '🌅',
      TrainingTimeOfDay.midday => '☀️',
      TrainingTimeOfDay.evening => '🌆',
    };
  }
}

class _ChoiceChip extends StatelessWidget {
  const _ChoiceChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
        decoration: BoxDecoration(
          color: selected ? AppColors.primary.withValues(alpha: 0.15) : null,
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.bgDarkSurface,
            width: selected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: selected ? AppColors.primary : AppColors.textPrimaryDark,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }
}

class _ChoiceTile extends StatelessWidget {
  const _ChoiceTile({
    required this.label,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });
  final String label;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: selected ? AppColors.primary.withValues(alpha: 0.1) : null,
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: selected ? AppColors.primary : Colors.transparent,
          width: 2,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        title: Text(label,
            style: TextStyle(
              fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
              color: selected ? AppColors.primary : AppColors.textPrimaryDark,
            )),
        subtitle: Text(subtitle,
            style: const TextStyle(
                color: AppColors.textSecondaryDark, fontSize: 12)),
        onTap: onTap,
      ),
    );
  }
}
