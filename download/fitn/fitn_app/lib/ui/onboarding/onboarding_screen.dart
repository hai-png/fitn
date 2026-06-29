/// Onboarding — 4-step wizard matching FitLife Hub design.
///
/// Steps:
/// 1. About Yourself (name, age, gender, weight, height)
/// 2. Define Target (goal, weekly frequency)
/// 3. Training Atmosphere (workout setting, gym finder + machine logger, activity level)
/// 4. Nutritional Foundation (diet type, allergies)
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fitn_engine/fitn_engine.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  int _step = 0;
  bool _loading = false;
  String _loadingMsg = 'Analyzing metabolic rate and physiological bio-markers...';

  // Step 1.
  final _nameCtrl = TextEditingController(text: '');
  final _ageCtrl = TextEditingController(text: '26');
  String _gender = 'male';
  final _weightCtrl = TextEditingController(text: '75');
  final _heightCtrl = TextEditingController(text: '175');

  // Step 2.
  String _goal = 'muscle-gain';
  int _frequency = 3;

  // Step 3.
  String _workoutPreference = 'gym'; // home | gym | outdoor | hybrid
  String _activityLevel = 'moderate'; // sedentary | light | moderate | active
  String? _selectedGymName;
  List<String> _availableMachines = [];

  // Step 4.
  String _dietType = 'anything'; // anything | vegetarian | vegan | keto | low-carb | gluten-free | mediterranean
  final _allergiesCtrl = TextEditingController();

  static const _nearbyGyms = [
    _GymOption(
      id: 'gym-1',
      name: 'Titan Iron Academy',
      distance: '0.4 miles away',
      rating: 4.9,
      address: '244 Heavy Metal Lane, District 4',
      description:
          'Hardcore powerlifting & bodybuilding sanctuary. Famous for its pristine equipment.',
      image:
          'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=300&auto=format&fit=crop&q=80',
      defaultMachines: [
        'Smith Machine',
        'Leg Press Machine',
        'Hack Squat',
        'Seated Row Machine',
        'Lat Pulldown',
        'Cable Crossover',
        'Pec Deck / Rear Delt Fly'
      ],
    ),
    _GymOption(
      id: 'gym-2',
      name: 'Pulse Athletic Club',
      distance: '1.2 miles away',
      rating: 4.7,
      address: '902 Wellness Blvd, Aether Plaza',
      description:
          'Luxury modern athletic center focusing on functional performance.',
      image:
          'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=300&auto=format&fit=crop&q=80',
      defaultMachines: [
        'Smith Machine',
        'Cable Crossover',
        'Lat Pulldown',
        'Leg Extension Machine',
        'Lying Leg Curl Machine',
        'Chest Press Machine'
      ],
    ),
    _GymOption(
      id: 'gym-3',
      name: 'Metro Flex Gym',
      distance: '2.1 miles away',
      rating: 4.8,
      address: '410 Barbells Way, Industrial Sector',
      description:
          'No-nonsense bodybuilding temple equipped with vintage heavy machinery.',
      image:
          'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=300&auto=format&fit=crop&q=80',
      defaultMachines: [
        'Hack Squat',
        'Smith Machine',
        'Leg Press Machine',
        'Lying Leg Curl Machine',
        'Seated Row Machine',
        'Pec Deck / Rear Delt Fly'
      ],
    ),
    _GymOption(
      id: 'gym-4',
      name: 'Aura Fit Studio',
      distance: '3.5 miles away',
      rating: 4.6,
      address: '12 Boutique Circle, Green Hills',
      description:
          'High-end coaching studio specializing in strength, aesthetics, and high-tech conditioning.',
      image:
          'https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=300&auto=format&fit=crop&q=80',
      defaultMachines: [
        'Cable Crossover',
        'Smith Machine',
        'Lat Pulldown',
        'Leg Extension Machine'
      ],
    ),
  ];

  static const _machineCategories = {
    'Push': [
      {'name': 'Smith Machine', 'desc': 'For secure heavy chest presses & controlled squats'},
      {'name': 'Chest Press Machine', 'desc': 'Isolates the pectoral muscles under stable load'},
      {'name': 'Pec Deck / Rear Delt Fly', 'desc': 'For safe chest flyes and posterior deltoid training'},
    ],
    'Pull': [
      {'name': 'Lat Pulldown', 'desc': 'Prime compound vertical pull for back widening'},
      {'name': 'Seated Row Machine', 'desc': 'Isolates the latissimus dorsi & middle back muscles'},
      {'name': 'Cable Crossover', 'desc': 'Provides constant cable tension for chest and arm exercises'},
    ],
    'Legs': [
      {'name': 'Leg Press Machine', 'desc': 'Heavy quadriceps and glute compound loading'},
      {'name': 'Hack Squat', 'desc': 'Decompresses spine while building massive quadricep force'},
      {'name': 'Leg Extension Machine', 'desc': 'Isolated single-joint quadricep builder'},
      {'name': 'Lying Leg Curl Machine', 'desc': 'Isolated single-joint hamstring builder'},
    ],
    'Arms': [
      {'name': 'Preacher Curl Bench', 'desc': 'Pins the biceps for ultimate peak contractions'},
    ],
  };

  @override
  void dispose() {
    _nameCtrl.dispose();
    _ageCtrl.dispose();
    _weightCtrl.dispose();
    _heightCtrl.dispose();
    _allergiesCtrl.dispose();
    super.dispose();
  }

  bool _isStepValid() {
    switch (_step) {
      case 0:
        return _nameCtrl.text.trim().isNotEmpty &&
            int.tryParse(_ageCtrl.text) != null &&
            double.tryParse(_weightCtrl.text) != null &&
            double.tryParse(_heightCtrl.text) != null;
      default:
        return true;
    }
  }

  Future<void> _submit() async {
    setState(() {
      _loading = true;
      _loadingMsg = 'Analyzing metabolic rate and physiological bio-markers...';
    });

    final msgs = [
      'Analyzing metabolic rate and physiological bio-markers...',
      'Engineering optimal compound workout splits...',
      'Matching macronutrient distributions with dietary targets...',
      'Synthesizing high-protein culinary recommendations...',
      'Polishing final custom coaching dashboard...',
    ];
    var msgIdx = 0;
    final timer = Stream.periodic(const Duration(milliseconds: 1200), (_) {
      msgIdx = (msgIdx + 1).clamp(0, msgs.length - 1);
      if (mounted) setState(() => _loadingMsg = msgs[msgIdx]);
    });

    try {
      // Map fitness-app inputs → fitn_engine UserProfile.
      final profile = UserProfile(
        age: int.parse(_ageCtrl.text),
        sex: _gender == 'female' ? Sex.female : Sex.male,
        heightCm: double.parse(_heightCtrl.text),
        weightKg: double.parse(_weightCtrl.text),
        activityLevel: _mapActivity(_activityLevel),
        trainingStatus: TrainingStatus
            .novice, // engine doesn't have "endurance" goal; default novice
        primaryGoal: _mapGoal(_goal),
        trainingDaysPerWeek: _frequency.clamp(2, 6),
        equipmentAccess: _mapEquipment(_workoutPreference),
        dietType: _mapDiet(_dietType),
        trainingTimeOfDay: TrainingTimeOfDay.evening,
      );
      final prefs = PlanPreferences(
        mealFrequency: 3,
        allergensToAvoid: _allergiesCtrl.text
            .split(',')
            .map((s) => s.trim().toLowerCase())
            .where((s) => s.isNotEmpty)
            .toList(),
        cuisinePreference: 'mediterranean',
        includePrePostWorkout: false,
      );
      await ref
          .read(appNotifierProvider.notifier)
          .setProfile(profile, name: _nameCtrl.text.trim());
      await ref.read(appNotifierProvider.notifier).setPreferences(prefs);
      await ref.read(appNotifierProvider.notifier).generatePlan();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to generate plan: $e')),
        );
      }
    } finally {
      timer.drain();
      if (mounted) setState(() => _loading = false);
    }
  }

  ActivityLevel _mapActivity(String s) => switch (s) {
        'sedentary' => ActivityLevel.sedentary,
        'light' => ActivityLevel.mostlySedentary,
        'moderate' => ActivityLevel.lightlyActive,
        'active' => ActivityLevel.active,
        _ => ActivityLevel.lightlyActive,
      };

  PrimaryGoal _mapGoal(String s) => switch (s) {
        'weight-loss' => PrimaryGoal.fatLoss,
        'muscle-gain' => PrimaryGoal.muscleGain,
        'strength' => PrimaryGoal.strength,
        'endurance' => PrimaryGoal.recomp,
        'general' => PrimaryGoal.maintenance,
        _ => PrimaryGoal.muscleGain,
      };

  EquipmentAccess _mapEquipment(String s) => switch (s) {
        'home' => EquipmentAccess.homeGym,
        'gym' => EquipmentAccess.fullGym,
        'outdoor' => EquipmentAccess.bodyweightOnly,
        'hybrid' => EquipmentAccess.homeGym,
        _ => EquipmentAccess.fullGym,
      };

  DietType _mapDiet(String s) => switch (s) {
        'vegan' => DietType.vegan,
        'vegetarian' => DietType.vegetarian,
        'anything' || 'keto' || 'low-carb' || 'gluten-free' || 'mediterranean' =>
          DietType.omnivore,
        _ => DietType.omnivore,
      };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FitnColors.cream,
      body: SafeArea(
        child: _loading ? _buildLoading() : _buildForm(),
      ),
    );
  }

  Widget _buildLoading() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: FitnColors.accent05,
                    shape: BoxShape.circle,
                  ),
                )
                    .animate(onPlay: (c) => c.repeat())
                    .scale(
                        begin: const Offset(1, 1),
                        end: const Offset(1.5, 1.5),
                        duration: 1200.ms),
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    border: Border.all(color: FitnColors.ink10, width: 1),
                  ),
                  child: Icon(LucideIcons.sparkles,
                      color: FitnColors.accent, size: 32),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Text('Formulating Your Plan',
                style: FitnText.headline.copyWith(fontSize: 24)),
            const SizedBox(height: 8),
            Text(
              _loadingMsg,
              textAlign: TextAlign.center,
              style: FitnText.serifItalic,
            )
                .animate(onPlay: (c) => c.repeat(reverse: true))
                .fade(begin: 0.4, end: 1, duration: 1500.ms),
            const SizedBox(height: 24),
            SizedBox(
              width: 200,
              child: LinearProgressIndicator(
                minHeight: 2,
                backgroundColor: FitnColors.ink05,
                color: FitnColors.ink,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildForm() {
    final steps = [
      ('Tell Us About Yourself',
          'Let\'s gather some basic metrics to construct your physical baseline.',
          LucideIcons.user),
      ('Define Your Target',
          'What is your primary fitness aspiration and weekly commitment?',
          LucideIcons.activity),
      ('Your Training Atmosphere',
          'Where do you work out and what is your daily movement style?',
          LucideIcons.dumbbell),
      ('Nutritional Foundation',
          'Your dietary habits and food sensitivities are vital.',
          LucideIcons.utensils),
    ];

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        // Header.
        Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: FitnColors.ink05,
                shape: BoxShape.circle,
                border: Border.all(color: FitnColors.ink10, width: 1),
              ),
              child: Icon(LucideIcons.compass, size: 16, color: FitnColors.ink),
            ),
            const SizedBox(width: 10),
            Text('FITN PERSONALIZED PLANNER',
                style: FitnText.microLabel.copyWith(fontSize: 9)),
          ],
        ),
        const SizedBox(height: 24),
        // Progress dots.
        Row(
          children: List.generate(4, (i) {
            return Container(
              margin: EdgeInsets.only(right: i < 3 ? 6 : 0),
              height: 4,
              width: i == _step ? 32 : (i < _step ? 16 : 8),
              color: i == _step
                  ? FitnColors.ink
                  : (i < _step ? FitnColors.ink40 : FitnColors.ink10),
            );
          }),
        ),
        const SizedBox(height: 24),
        // Title + subtitle.
        Text(
          steps[_step].$1,
          style: FitnText.headline.copyWith(fontSize: 28),
        ),
        const SizedBox(height: 8),
        Text(steps[_step].$2, style: FitnText.serifItalic),
        const SizedBox(height: 24),
        // Step content.
        _buildStepContent(),
        const SizedBox(height: 24),
        // Footer nav.
        Row(
          children: [
            if (_step > 0)
              OutlinedButton(
                onPressed: () => setState(() => _step--),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(0, 48),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(LucideIcons.chevronLeft, size: 16),
                    const SizedBox(width: 6),
                    Text('BACK', style: FitnText.buttonLabel.copyWith(color: FitnColors.ink)),
                  ],
                ),
              )
            else
              const Spacer(),
            const Spacer(),
            ElevatedButton(
              onPressed: _isStepValid()
                  ? () {
                      if (_step < 3) {
                        setState(() => _step++);
                      } else {
                        _submit();
                      }
                    }
                  : null,
              style: ElevatedButton.styleFrom(
                backgroundColor:
                    _step < 3 ? FitnColors.ink : FitnColors.accent,
                minimumSize: const Size(0, 48),
                padding:
                    const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (_step < 3) ...[
                    Text('NEXT STEP', style: FitnText.buttonLabel),
                    const SizedBox(width: 6),
                    Icon(LucideIcons.chevronRight, size: 16, color: Colors.white),
                  ] else ...[
                    Icon(LucideIcons.sparkles, size: 16, color: Colors.white),
                    const SizedBox(width: 6),
                    Text('BUILD MY PLANS', style: FitnText.buttonLabel),
                    const SizedBox(width: 6),
                    Icon(LucideIcons.arrowRight, size: 16, color: Colors.white),
                  ],
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStepContent() {
    return switch (_step) {
      0 => _buildBasicsStep(),
      1 => _buildTargetStep(),
      2 => _buildTrainingAtmosphereStep(),
      3 => _buildNutritionStep(),
      _ => const SizedBox(),
    };
  }

  Widget _buildBasicsStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label('Your Name'),
        TextField(
          controller: _nameCtrl,
          decoration: const InputDecoration(hintText: 'e.g. John Doe'),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: _label('Age')),
            const SizedBox(width: 16),
            Expanded(child: _label('Gender')),
          ],
        ),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _ageCtrl,
                keyboardType: TextInputType.number,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(color: FitnColors.ink15, width: 1),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _gender,
                    isExpanded: true,
                    style: GoogleFonts.inter(
                        fontSize: 13, color: FitnColors.ink),
                    items: const [
                      DropdownMenuItem(value: 'male', child: Text('Male')),
                      DropdownMenuItem(value: 'female', child: Text('Female')),
                      DropdownMenuItem(value: 'other', child: Text('Non-binary')),
                    ],
                    onChanged: (v) => setState(() => _gender = v ?? 'male'),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: _label('Weight (kg)')),
            const SizedBox(width: 16),
            Expanded(child: _label('Height (cm)')),
          ],
        ),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _weightCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: TextField(
                controller: _heightCtrl,
                keyboardType: TextInputType.number,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTargetStep() {
    final goals = [
      ('weight-loss', 'Fat Shred & Slimming', 'Burn calories, boost metabolism, lose body fat'),
      ('muscle-gain', 'Lean Muscle Hypertrophy', 'Build size, increase muscle mass, density'),
      ('strength', 'Pure Mechanical Strength', 'Lift heavier, improve power, core stabilization'),
      ('endurance', 'Cardio & Stamina Builder', 'Boost VO2 max, endurance, lung capacity'),
      ('general', 'Active Wellness & Tonus', 'Feel energetic, flexible, overall mobility'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label('Primary Aspiration'),
        const SizedBox(height: 8),
        ...goals.map((g) {
          final selected = _goal == g.$1;
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: InkWell(
              onTap: () => setState(() => _goal = g.$1),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: selected ? FitnColors.ink : Colors.white,
                  border: Border.all(
                      color: selected ? FitnColors.ink : FitnColors.ink10,
                      width: 1),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(g.$2.toUpperCase(),
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: selected ? Colors.white : FitnColors.ink,
                        )),
                    const SizedBox(height: 4),
                    Text(g.$3,
                        style: FitnText.serifItalic.copyWith(
                          color: selected ? Colors.white70 : FitnColors.ink50,
                          fontSize: 11,
                        )),
                  ],
                ),
              ),
            ),
          );
        }),
        const SizedBox(height: 16),
        _label('Weekly Workout Frequency'),
        const SizedBox(height: 8),
        Row(
          children: [2, 3, 4, 5].map((n) {
            final selected = _frequency == n;
            return Expanded(
              child: Padding(
                padding: EdgeInsets.only(right: n < 5 ? 8 : 0),
                child: InkWell(
                  onTap: () => setState(() => _frequency = n),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    decoration: BoxDecoration(
                      color: selected ? FitnColors.ink : Colors.white,
                      border: Border.all(
                          color: selected ? FitnColors.ink : FitnColors.ink10,
                          width: 1),
                    ),
                    child: Text(
                      '$n DAYS',
                      textAlign: TextAlign.center,
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: selected ? Colors.white : FitnColors.ink,
                      ),
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildTrainingAtmosphereStep() {
    final prefs = [
      ('home', 'Home Gym (Calisthenics & Minimal Equipment)',
          'Bodyweight focus, bands, chairs, dumbbells'),
      ('gym', 'Commercial Gym (Barbells, Cables & Machines)',
          'Full power rack access, cables, leg machines'),
      ('outdoor', 'Outdoor Arena (Bars, Parks & Running)',
          'Aerobic base, pullup bars, sprint loops'),
      ('hybrid', 'Hybrid Versatility',
          'A blend of home bodyweight and commercial machinery'),
    ];
    final activities = [
      ('sedentary', 'Sedentary', 'Desk job, few walks'),
      ('light', 'Lightly Active', '1-2h light walk/day'),
      ('moderate', 'Moderately Active', 'Active stands, daily run'),
      ('active', 'Very Athlete Active', 'Labor work or heavy training'),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label('Workout Setting Preference'),
        const SizedBox(height: 8),
        ...prefs.map((p) {
          final selected = _workoutPreference == p.$1;
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: InkWell(
              onTap: () {
                setState(() {
                  _workoutPreference = p.$1;
                  if (p.$1 != 'gym') {
                    _selectedGymName = null;
                    _availableMachines = const [];
                  } else if (_selectedGymName == null) {
                    _selectedGymName = _nearbyGyms.first.name;
                    _availableMachines = _nearbyGyms.first.defaultMachines;
                  }
                });
              },
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: selected ? FitnColors.ink : Colors.white,
                  border: Border.all(
                      color: selected ? FitnColors.ink : FitnColors.ink10,
                      width: 1),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(p.$2.toUpperCase(),
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: selected ? Colors.white : FitnColors.ink,
                        )),
                    const SizedBox(height: 4),
                    Text(p.$3,
                        style: FitnText.serifItalic.copyWith(
                          color: selected ? Colors.white70 : FitnColors.ink50,
                          fontSize: 11,
                        )),
                  ],
                ),
              ),
            ),
          );
        }),
        if (_workoutPreference == 'gym') ...[
          const SizedBox(height: 20),
          Row(
            children: [
              Icon(LucideIcons.mapPin, size: 14, color: FitnColors.accent),
              const SizedBox(width: 6),
              Text('NEARBY GYM FINDER & LOGGER', style: FitnText.microLabel),
            ],
          ),
          const SizedBox(height: 8),
          ..._nearbyGyms.map((g) {
            final selected = _selectedGymName == g.name;
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: InkWell(
                onTap: () {
                  setState(() {
                    _selectedGymName = g.name;
                    _availableMachines = g.defaultMachines;
                  });
                },
                child: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(
                        color: selected ? FitnColors.accent : FitnColors.ink10,
                        width: 1),
                  ),
                  child: Row(
                    children: [
                      ClipRRect(
                        child: Image.network(g.image,
                            width: 48, height: 48, fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => Container(
                                width: 48,
                                height: 48,
                                color: FitnColors.ink05,
                                child: Icon(LucideIcons.dumbbell, size: 18))),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(g.name.toUpperCase(),
                                      style: GoogleFonts.inter(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w700,
                                          color: FitnColors.ink)),
                                ),
                                Text(g.distance,
                                    style: FitnText.monoSmall.copyWith(
                                        fontSize: 8, color: FitnColors.ink60)),
                              ],
                            ),
                            const SizedBox(height: 2),
                            Text(g.address, style: FitnText.serifItalic.copyWith(fontSize: 10)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          }),
          if (_selectedGymName != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(color: FitnColors.ink10, width: 1),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('LOG $_selectedGymName MACHINES',
                      style: FitnText.microLabel),
                  const SizedBox(height: 12),
                  ..._machineCategories.entries.expand((cat) {
                    return cat.value.map((m) {
                      final isChecked = _availableMachines.contains(m['name']);
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: InkWell(
                          onTap: () {
                            setState(() {
                              if (isChecked) {
                                _availableMachines =
                                    _availableMachines.where((x) => x != m['name']).toList();
                              } else {
                                _availableMachines = [..._availableMachines, m['name']!];
                              }
                            });
                          },
                          child: Row(
                            children: [
                              Container(
                                width: 16,
                                height: 16,
                                decoration: BoxDecoration(
                                  color: isChecked ? FitnColors.ink : Colors.white,
                                  border: Border.all(
                                      color: isChecked ? FitnColors.ink : FitnColors.ink30,
                                      width: 1),
                                ),
                                child: isChecked
                                    ? Icon(LucideIcons.check,
                                        size: 12, color: Colors.white)
                                    : null,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(m['name']!.toUpperCase(),
                                        style: GoogleFonts.inter(
                                            fontSize: 10,
                                            fontWeight: FontWeight.w700,
                                            color: FitnColors.ink)),
                                    Text(m['desc']!,
                                        style: FitnText.serifItalic.copyWith(fontSize: 9)),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    });
                  }),
                ],
              ),
            ),
          ],
        ],
        const SizedBox(height: 20),
        _label('Daily Baseline Activity Level'),
        const SizedBox(height: 8),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
          childAspectRatio: 2.4,
          children: activities.map((a) {
            final selected = _activityLevel == a.$1;
            return InkWell(
              onTap: () => setState(() => _activityLevel = a.$1),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: selected ? FitnColors.ink : Colors.white,
                  border: Border.all(
                      color: selected ? FitnColors.ink : FitnColors.ink10,
                      width: 1),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(a.$2.toUpperCase(),
                        style: GoogleFonts.inter(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: selected ? Colors.white : FitnColors.ink)),
                    const SizedBox(height: 2),
                    Text(a.$3,
                        style: FitnText.serifItalic.copyWith(
                            fontSize: 10,
                            color: selected ? Colors.white70 : FitnColors.ink50)),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildNutritionStep() {
    final diets = [
      ('anything', 'Anything / Balanced'),
      ('vegetarian', 'Vegetarian'),
      ('vegan', 'Vegan'),
      ('keto', 'Ketogenic (Low Carb)'),
      ('low-carb', 'Low Carb (Moderate)'),
      ('gluten-free', 'Gluten-Free'),
      ('mediterranean', 'Mediterranean'),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _label('Dietary Category'),
        const SizedBox(height: 8),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
          childAspectRatio: 3.0,
          children: diets.map((d) {
            final selected = _dietType == d.$1;
            return InkWell(
              onTap: () => setState(() => _dietType = d.$1),
              child: Container(
                alignment: Alignment.center,
                padding: const EdgeInsets.symmetric(horizontal: 8),
                decoration: BoxDecoration(
                  color: selected ? FitnColors.ink : Colors.white,
                  border: Border.all(
                      color: selected ? FitnColors.ink : FitnColors.ink10,
                      width: 1),
                ),
                child: Text(d.$2.toUpperCase(),
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: selected ? Colors.white : FitnColors.ink)),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
        _label('Allergies & Food Sensitivities'),
        TextField(
          controller: _allergiesCtrl,
          decoration: const InputDecoration(
              hintText: 'e.g. Peanuts, Dairy, Seafood (or leave blank)'),
        ),
        const SizedBox(height: 8),
        Text(
          'Our paid meal delivery service tab will badge or restrict recommended preps with these triggers.',
          style: FitnText.serifItalic.copyWith(fontSize: 10),
        ),
      ],
    );
  }

  Widget _label(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(text.toUpperCase(), style: FitnText.microLabel),
    );
  }
}

class _GymOption {
  const _GymOption({
    required this.id,
    required this.name,
    required this.distance,
    required this.rating,
    required this.address,
    required this.description,
    required this.image,
    required this.defaultMachines,
  });
  final String id;
  final String name;
  final String distance;
  final double rating;
  final String address;
  final String description;
  final String image;
  final List<String> defaultMachines;
}
