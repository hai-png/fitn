/// Workout templates — program presets + split templates + exercise database.
/// Ported from fitness-app's workoutTemplates.ts.
library;

import 'package:fitn_engine/fitn_engine.dart';

class ExerciseDbItem {
  const ExerciseDbItem({
    required this.name,
    required this.targetMuscle,
    required this.instruction,
    required this.restSeconds,
    required this.sets,
    required this.reps,
    required this.videoUrl,
    required this.steps,
  });
  final String name;
  final String targetMuscle;
  final String instruction;
  final int restSeconds;
  final int sets;
  final String reps;
  final String videoUrl;
  final List<String> steps;
}

/// Curated exercise database for the custom split builder.
class WorkoutTemplates {
  WorkoutTemplates._();

  static const List<ExerciseDbItem> exerciseDatabase = [
    // CHEST
    ExerciseDbItem(
      name: 'Flat Barbell Bench Press',
      targetMuscle: 'Chest',
      instruction: 'Touch lower sternum and press up vertically.',
      restSeconds: 120,
      sets: 3,
      reps: '6-8 reps',
      videoUrl: 'flat-bench-press',
      steps: [
        'Lie flat, eyes under bar, grip slightly wider than shoulders.',
        'Pull shoulder blades together, plant feet firmly on the floor.',
        'Unrack bar, lower slowly to lower sternum/nipple line.',
        'Drive heels and press bar forcefully to locked out start position.',
      ],
    ),
    ExerciseDbItem(
      name: 'Incline Dumbbell Press',
      targetMuscle: 'Chest',
      instruction: 'Keep elbows at 45 degrees, squeeze chest at peak.',
      restSeconds: 90,
      sets: 4,
      reps: '8-10 reps',
      videoUrl: 'incline-dumbbell-press',
      steps: [
        'Set the bench to a 30-degree incline.',
        'Sit back with dumbbells at chest height, elbows under wrists.',
        'Press dumbbells straight up, squeezing chest at the top.',
        'Lower under control until dumbbells touch outer chest.',
      ],
    ),
    ExerciseDbItem(
      name: 'Cable Chest Flys',
      targetMuscle: 'Chest',
      instruction: 'Focus on a deep stretch and wrapping arms around a tree.',
      restSeconds: 60,
      sets: 3,
      reps: '12-15 reps',
      videoUrl: 'cable-chest-fly',
      steps: [
        'Set pulleys to shoulder-height, stand midway with one foot forward.',
        'Grip handles, maintain a slight bend in your elbows.',
        'Bring hands together in a wide hugging arc in front of chest.',
        'Squeeze for 1s, then return slowly to feel a deep stretch.',
      ],
    ),
    // BACK
    ExerciseDbItem(
      name: 'Lat Pulldown (Wide Grip)',
      targetMuscle: 'Lats',
      instruction: 'Pull with your elbows, retracting scapula fully.',
      restSeconds: 90,
      sets: 4,
      reps: '10-12 reps',
      videoUrl: 'lat-pulldown',
      steps: [
        'Sit, adjust knee pads, grip bar wider than shoulder-width.',
        'Lean back slightly (10-15 degrees), keep core tight.',
        'Pull bar down to upper chest, leading with elbows.',
        'Squeeze lats, then let bar return slowly with full stretch.',
      ],
    ),
    ExerciseDbItem(
      name: 'Seated Cable Row',
      targetMuscle: 'Mid Back',
      instruction: 'Keep spine neutral, pull handle to belly button.',
      restSeconds: 90,
      sets: 3,
      reps: '10-12 reps',
      videoUrl: 'seated-cable-row',
      steps: [
        'Sit on bench, feet on footplates, knees slightly bent.',
        'Grip close-grip attachment, sit tall with neutral spine.',
        'Pull handle to lower abdomen, pulling shoulders back.',
        'Squeeze shoulder blades, then slowly return to start.',
      ],
    ),
    ExerciseDbItem(
      name: 'Dumbbell Single-Arm Row',
      targetMuscle: 'Upper Back',
      instruction: 'Support knee on bench, pull weight to hip pocket.',
      restSeconds: 90,
      sets: 3,
      reps: '8-10 reps',
      videoUrl: 'dumbbell-row',
      steps: [
        'Place same-side knee and hand on bench, other foot flat on floor.',
        'Hold dumbbell with straight arm, spine neutral.',
        'Pull elbow up and back towards your hip pocket.',
        'Squeeze upper back, then lower dumbbell slowly.',
      ],
    ),
    // LEGS
    ExerciseDbItem(
      name: 'Barbell Back Squats',
      targetMuscle: 'Quads',
      instruction: 'Hips back, descend to parallel, press through mid-foot.',
      restSeconds: 120,
      sets: 4,
      reps: '6-8 reps',
      videoUrl: 'barbell-back-squat',
      steps: [
        'Position bar on upper traps, grip tightly, lift off rack.',
        'Step back, feet shoulder-width, toes flared 15 degrees.',
        'Hinge hips back, bend knees, descend deep to parallel.',
        'Drive through mid-foot, stand up, keeping chest tall.',
      ],
    ),
    ExerciseDbItem(
      name: 'Romanian Deadlifts (RDL)',
      targetMuscle: 'Hamstrings',
      instruction: 'Hinge at hips, keep bar close to shins, squeeze glutes.',
      restSeconds: 90,
      sets: 3,
      reps: '10-12 reps',
      videoUrl: 'romanian-deadlift',
      steps: [
        'Stand holding barbell at hips, feet hip-width apart.',
        'Push hips backward, keeping knees soft but static.',
        'Lower barbell along thighs, keeping spine completely flat.',
        'Once hamstrings stretch fully, drive hips forward and stand.',
      ],
    ),
    ExerciseDbItem(
      name: 'Leg Extensions',
      targetMuscle: 'Quads',
      instruction: 'Squeeze quads for 1 second at full extension.',
      restSeconds: 60,
      sets: 3,
      reps: '15 reps',
      videoUrl: 'leg-extension',
      steps: [
        'Sit on machine, back flat, shins behind roller pad.',
        'Grip side handles, engage core, extend legs upward fully.',
        'Squeeze quadriceps intensely at the peak for 1 second.',
        'Lower weight slowly to starting position under control.',
      ],
    ),
    // SHOULDERS
    ExerciseDbItem(
      name: 'Dumbbell Shoulder Press',
      targetMuscle: 'Shoulders',
      instruction: 'Press straight up, do not flare elbows excessively.',
      restSeconds: 90,
      sets: 4,
      reps: '8-10 reps',
      videoUrl: 'dumbbell-shoulder-press',
      steps: [
        'Sit on bench with vertical back support, feet flat.',
        'Hold dumbbells at shoulder height, elbows slightly forward.',
        'Press dumbbells straight up, locking overhead.',
        'Lower with control to ear level to complete the rep.',
      ],
    ),
    ExerciseDbItem(
      name: 'Dumbbell Lateral Raises',
      targetMuscle: 'Side Deltoid',
      instruction: 'Lead with elbows, keep pinkies slightly elevated.',
      restSeconds: 60,
      sets: 4,
      reps: '12-15 reps',
      videoUrl: 'lateral-raise',
      steps: [
        'Stand tall, dumbbells at sides, slight hinge forward.',
        'Raise arms to the sides, leading with your elbows.',
        'Keep arms almost straight, tilt pinkies up at peak.',
        'Lower dumbbells slowly, avoiding swinging for momentum.',
      ],
    ),
    ExerciseDbItem(
      name: 'Face Pulls',
      targetMuscle: 'Rear Deltoid',
      instruction: 'Pull rope to nose, flaring elbows out, squeeze rear delts.',
      restSeconds: 60,
      sets: 3,
      reps: '15 reps',
      videoUrl: 'cable-face-pull',
      steps: [
        'Attach rope to high pulley, grasp ends with palms facing down.',
        'Step back, engage core, hold arms fully extended.',
        'Pull rope towards bridge of nose, flaring elbows wide.',
        'External rotate hands at peak, squeeze rear delts.',
      ],
    ),
    // ARMS
    ExerciseDbItem(
      name: 'Dumbbell Incline Bicep Curls',
      targetMuscle: 'Biceps',
      instruction: 'Full stretch at bottom, pin elbows to sides.',
      restSeconds: 60,
      sets: 3,
      reps: '10-12 reps',
      videoUrl: 'incline-bicep-curl',
      steps: [
        'Lie back on a 45-degree incline bench with dumbbells.',
        'Let arms hang straight down, palms facing forward.',
        'Curl dumbbells up, keeping elbows pinned in place.',
        'Squeeze biceps, then lower with full eccentric control.',
      ],
    ),
    ExerciseDbItem(
      name: 'Tricep Overhead Cable Press',
      targetMuscle: 'Triceps',
      instruction: 'Extend overhead fully, focus on the long head.',
      restSeconds: 60,
      sets: 3,
      reps: '12-15 reps',
      videoUrl: 'overhead-tricep-extension',
      steps: [
        'Attach rope to low pulley, face away, hold rope behind neck.',
        'Step forward into split stance, lean torso slightly.',
        'Extend elbows fully overhead, squeezing triceps at peak.',
        'Lower rope slowly behind head, feeling deep stretch.',
      ],
    ),
    // CORE
    ExerciseDbItem(
      name: 'Hanging Knee Raises',
      targetMuscle: 'Lower Abs',
      instruction: 'Avoid swinging; curl hips upward at peak.',
      restSeconds: 60,
      sets: 3,
      reps: '12-15 reps',
      videoUrl: 'hanging-knee-raise',
      steps: [
        'Hang from pull-up bar with overhand grip, arms straight.',
        'Engage shoulders, avoid swinging momentum.',
        'Raise knees towards chest, tucking hips up at top.',
        'Lower legs slowly to vertical under perfect control.',
      ],
    ),
    ExerciseDbItem(
      name: 'Plank Hold',
      targetMuscle: 'Core',
      instruction: 'Squeeze glutes, quads, and pull belly button to spine.',
      restSeconds: 60,
      sets: 3,
      reps: '60 seconds',
      videoUrl: 'plank-hold',
      steps: [
        'Place forearms on floor, shoulders stacked over elbows.',
        'Extend legs back, toes tucked, hips level with shoulders.',
        'Squeeze glutes, pull belly button up, tighten thighs.',
        'Maintain deep, steady breathing for the duration.',
      ],
    ),
    // CARDIO
    ExerciseDbItem(
      name: 'Stationary Bike Sprint Intervals',
      targetMuscle: 'Cardio',
      instruction: 'Pedal light for 2 mins, then sprint for 30s.',
      restSeconds: 60,
      sets: 4,
      reps: '8 mins',
      videoUrl: 'bike-sprints',
      steps: [
        'Warm up at light intensity for 2 minutes.',
        'Increase resistance, sprint at max RPM for 30 seconds.',
        'Drop resistance, spin slowly for 30 seconds to recover.',
        'Repeat intervals, then cool down for 1 minute.',
      ],
    ),
  ];

  static const List<String> categories = [
    'Chest',
    'Back',
    'Legs',
    'Shoulders',
    'Arms',
    'Core',
    'Cardio'
  ];
}

/// Program preset — a pre-built multi-week training program.
class ProgramPreset {
  const ProgramPreset({
    required this.name,
    required this.description,
    required this.durationWeeks,
    required this.goal,
    required this.splitType,
    required this.daysPerWeek,
  });
  final String name;
  final String description;
  final int durationWeeks;
  final String goal;
  final String splitType;
  final int daysPerWeek;
}

class ProgramPresets {
  ProgramPresets._();

  static const List<ProgramPreset> all = [
    ProgramPreset(
      name: 'Hypertrophy Builder',
      description:
          '4-day upper/lower split focused on muscle accumulation. Moderate volume, progressive overload weekly.',
      durationWeeks: 8,
      goal: 'muscle-gain',
      splitType: 'Upper / Lower',
      daysPerWeek: 4,
    ),
    ProgramPreset(
      name: 'Powerlifting Peak',
      description:
          '3-day full-body strength block. Low reps, heavy compound lifts, linear progression.',
      durationWeeks: 12,
      goal: 'strength',
      splitType: 'Full Body',
      daysPerWeek: 3,
    ),
    ProgramPreset(
      name: 'Fat Shred Circuit',
      description:
          '5-day PPL + cardio hybrid. High volume, short rest, metabolic conditioning focus.',
      durationWeeks: 6,
      goal: 'weight-loss',
      splitType: 'Push / Pull / Legs',
      daysPerWeek: 5,
    ),
    ProgramPreset(
      name: 'Wellness Foundation',
      description:
          '2-day full-body maintenance plan. Light volume, balanced movements, sustainable frequency.',
      durationWeeks: 4,
      goal: 'general',
      splitType: 'Full Body',
      daysPerWeek: 2,
    ),
    ProgramPreset(
      name: 'Endurance Engine',
      description:
          '4-day hybrid strength + cardio block. Compound lifts + zone 2 work for VO2 max.',
      durationWeeks: 10,
      goal: 'endurance',
      splitType: 'Upper / Lower',
      daysPerWeek: 4,
    ),
  ];
}
