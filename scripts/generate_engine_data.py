#!/usr/bin/env python3
"""Generate the missing JSON data files for fitn_engine assets.

Produces:
- split_designs.json (8 entries per spec §9.4)
- movement_patterns.json (40 entries per spec §9.4)
- food_database.json (filler foods per spec §4.5)
- pre_post_workout_recipes.json (16 entries per spec §9.4)
- recipe_database.json (curated subset — small representative sample)
"""
import json
import os

ASSETS = "/home/z/my-project/download/fitn/fitn_engine/assets"
os.makedirs(ASSETS, exist_ok=True)


# ============================================================
# 1. split_designs.json (8 split designs)
# ============================================================
SPLIT_DESIGNS = [
    {
        "name": "full_body_2day",
        "split_type": "full_body",
        "days_per_week": 2,
        "description": "Two-day full-body split for beginners. Trains every major muscle group each session, 2-3x per week for optimal frequency.",
        "templates": [
            {
                "name": "Full Body A",
                "focus": "Strength + Hypertrophy",
                "day_type": None,
                "slots": [
                    {"name": "Squat Primary", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Bench Press Primary", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Row Primary", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Overhead Press Accessory", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Hip Hinge Accessory", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes", "lower_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Core Work", "primary_muscle": "abs", "pattern": "core_anti_extension", "category": "accessory", "sets": 3, "secondary_muscles": ["obliques"], "force_type_hint": None, "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Full Body B",
                "focus": "Strength + Hypertrophy",
                "day_type": None,
                "slots": [
                    {"name": "Deadlift Primary", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Incline Press Primary", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Pull-Up / Lat Pulldown", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Lunge Accessory", "primary_muscle": "quads", "pattern": "lunge", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Curl Accessory", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Triceps Accessory", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
        ],
        "rest_days": [3, 4, 5, 6, 7],
        "suitable_for_experience": ["beginner", "novice", "intermediate"],
        "suitable_for_goals": ["general_fitness", "maintenance", "muscle_gain", "strength", "fat_loss", "recomp"],
    },
    {
        "name": "full_body_3day",
        "split_type": "full_body",
        "days_per_week": 3,
        "description": "Three-day full-body split. The gold standard for beginner-to-novice trainees.",
        "templates": [
            {
                "name": "Full Body A",
                "focus": "Squat emphasis",
                "day_type": "heavy",
                "slots": [
                    {"name": "Squat Primary", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Bench Press Primary", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Row Primary", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Core", "primary_muscle": "abs", "pattern": "core_anti_extension", "category": "accessory", "sets": 3, "secondary_muscles": ["obliques"], "force_type_hint": None, "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Full Body B",
                "focus": "Deadlift emphasis",
                "day_type": "moderate",
                "slots": [
                    {"name": "Deadlift Primary", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Overhead Press Primary", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "traps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Pull-Up / Lat Pulldown", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Lunge Accessory", "primary_muscle": "quads", "pattern": "lunge", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Full Body C",
                "focus": "Bench emphasis",
                "day_type": "light",
                "slots": [
                    {"name": "Front Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "core"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Incline Press", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Seated Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Arm Accessory Superset", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                ],
            },
        ],
        "rest_days": [4, 5, 7],
        "suitable_for_experience": ["beginner", "novice", "intermediate"],
        "suitable_for_goals": ["general_fitness", "maintenance", "muscle_gain", "strength", "fat_loss", "recomp"],
    },
    {
        "name": "upper_lower_4day",
        "split_type": "upper_lower",
        "days_per_week": 4,
        "description": "Four-day upper/lower split. Ideal for novice-to-intermediate trainees seeking a balance of frequency and recovery.",
        "templates": [
            {
                "name": "Upper A (Heavy)",
                "focus": "Strength + Hypertrophy",
                "day_type": "heavy",
                "slots": [
                    {"name": "Bench Press", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Overhead Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Pull-Up", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Biceps Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Triceps Extension", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Lower A (Heavy)",
                "focus": "Strength + Hypertrophy",
                "day_type": "heavy",
                "slots": [
                    {"name": "Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Romanian Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Leg Press", "primary_muscle": "quads", "pattern": "squat", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Calf Raise", "primary_muscle": "calves", "pattern": "ankle_plantarflexion", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Core", "primary_muscle": "abs", "pattern": "core_anti_extension", "category": "accessory", "sets": 3, "secondary_muscles": ["obliques"], "force_type_hint": None, "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Upper B (Volume)",
                "focus": "Hypertrophy",
                "day_type": "moderate",
                "slots": [
                    {"name": "Incline DB Press", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Lat Pulldown", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Cable Fly", "primary_muscle": "chest", "pattern": "chest_fly", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Lateral Raise", "primary_muscle": "shoulders", "pattern": "lateral_raise", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Rear Delt Fly", "primary_muscle": "rear_delts", "pattern": "rear_delt", "category": "accessory", "sets": 3, "secondary_muscles": ["upper_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Lower B (Volume)",
                "focus": "Hypertrophy",
                "day_type": "moderate",
                "slots": [
                    {"name": "Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Front Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "core"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Leg Curl", "primary_muscle": "hamstrings", "pattern": "knee_flexion", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Hip Thrust", "primary_muscle": "glutes", "pattern": "hip_thrust", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Calf Raise", "primary_muscle": "calves", "pattern": "ankle_plantarflexion", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
        ],
        "rest_days": [3, 7],
        "suitable_for_experience": ["novice", "intermediate", "advanced"],
        "suitable_for_goals": ["muscle_gain", "strength", "recomp", "maintenance", "fat_loss"],
    },
    {
        "name": "push_pull_legs_3day",
        "split_type": "ppl",
        "days_per_week": 3,
        "description": "Three-day push/pull/legs. Frequency is lower but each session is highly focused.",
        "templates": [
            {
                "name": "Push",
                "focus": "Chest, Shoulders, Triceps",
                "day_type": None,
                "slots": [
                    {"name": "Bench Press", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Overhead Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Incline DB Press", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Lateral Raise", "primary_muscle": "shoulders", "pattern": "lateral_raise", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Triceps Extension", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Pull",
                "focus": "Back, Biceps",
                "day_type": None,
                "slots": [
                    {"name": "Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Pull-Up", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Barbell Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Rear Delt Fly", "primary_muscle": "rear_delts", "pattern": "rear_delt", "category": "accessory", "sets": 3, "secondary_muscles": ["upper_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Biceps Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 4, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Legs",
                "focus": "Quads, Hamstrings, Glutes, Calves",
                "day_type": None,
                "slots": [
                    {"name": "Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Romanian Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Leg Press", "primary_muscle": "quads", "pattern": "squat", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Leg Curl", "primary_muscle": "hamstrings", "pattern": "knee_flexion", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Calf Raise", "primary_muscle": "calves", "pattern": "ankle_plantarflexion", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Core", "primary_muscle": "abs", "pattern": "core_anti_extension", "category": "accessory", "sets": 3, "secondary_muscles": ["obliques"], "force_type_hint": None, "is_focus_emphasis": False},
                ],
            },
        ],
        "rest_days": [4, 5, 6, 7],
        "suitable_for_experience": ["novice", "intermediate"],
        "suitable_for_goals": ["muscle_gain", "strength", "recomp", "maintenance"],
    },
    {
        "name": "push_pull_legs_6day",
        "split_type": "pplX2",
        "days_per_week": 6,
        "description": "Six-day push/pull/legs performed twice per week. High frequency, high volume — for intermediate+ trainees with strong recovery.",
        "templates": [
            {
                "name": "Push A (Heavy)",
                "focus": "Strength",
                "day_type": "heavy",
                "slots": [
                    {"name": "Bench Press", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 5, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Overhead Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Incline DB Press", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Lateral Raise", "primary_muscle": "shoulders", "pattern": "lateral_raise", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Triceps Extension", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Pull A (Heavy)",
                "focus": "Strength",
                "day_type": "heavy",
                "slots": [
                    {"name": "Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Weighted Pull-Up", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Pendlay Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Rear Delt Fly", "primary_muscle": "rear_delts", "pattern": "rear_delt", "category": "accessory", "sets": 3, "secondary_muscles": ["upper_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Biceps Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 4, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Legs A (Heavy)",
                "focus": "Strength",
                "day_type": "heavy",
                "slots": [
                    {"name": "Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 5, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Romanian Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Leg Press", "primary_muscle": "quads", "pattern": "squat", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Leg Curl", "primary_muscle": "hamstrings", "pattern": "knee_flexion", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Calf Raise", "primary_muscle": "calves", "pattern": "ankle_plantarflexion", "category": "accessory", "sets": 5, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Push B (Volume)",
                "focus": "Hypertrophy",
                "day_type": "moderate",
                "slots": [
                    {"name": "Incline DB Press", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Cable Fly", "primary_muscle": "chest", "pattern": "chest_fly", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "DB Shoulder Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Lateral Raise", "primary_muscle": "shoulders", "pattern": "lateral_raise", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Triceps Pushdown", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Pull B (Volume)",
                "focus": "Hypertrophy",
                "day_type": "moderate",
                "slots": [
                    {"name": "Lat Pulldown", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Seated Cable Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Face Pull", "primary_muscle": "rear_delts", "pattern": "rear_delt", "category": "accessory", "sets": 3, "secondary_muscles": ["upper_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Hammer Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["forearms", "brachialis"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                    {"name": "Incline Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                ],
            },
            {
                "name": "Legs B (Volume)",
                "focus": "Hypertrophy",
                "day_type": "moderate",
                "slots": [
                    {"name": "Front Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "core"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Hip Thrust", "primary_muscle": "glutes", "pattern": "hip_thrust", "category": "compound_primary", "sets": 4, "secondary_muscles": ["hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Walking Lunge", "primary_muscle": "quads", "pattern": "lunge", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Leg Extension", "primary_muscle": "quads", "pattern": "knee_extension", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                    {"name": "Seated Calf Raise", "primary_muscle": "calves", "pattern": "ankle_plantarflexion", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                ],
            },
        ],
        "rest_days": [7],
        "suitable_for_experience": ["intermediate", "advanced"],
        "suitable_for_goals": ["muscle_gain", "strength", "recomp"],
    },
    {
        "name": "ppl_upper_lower_5day",
        "split_type": "pushPullLegsUpperLower",
        "days_per_week": 5,
        "description": "Five-day hybrid: PPL + Upper/Lower. Balances volume and frequency for intermediate trainees.",
        "templates": [
            {"name": "Push", "focus": "Chest/Shoulders/Triceps", "day_type": None, "slots": [
                {"name": "Bench Press", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Overhead Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Cable Fly", "primary_muscle": "chest", "pattern": "chest_fly", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Lateral Raise", "primary_muscle": "shoulders", "pattern": "lateral_raise", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Triceps Extension", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
            ]},
            {"name": "Pull", "focus": "Back/Biceps", "day_type": None, "slots": [
                {"name": "Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Pull-Up", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Barbell Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Rear Delt Fly", "primary_muscle": "rear_delts", "pattern": "rear_delt", "category": "accessory", "sets": 3, "secondary_muscles": ["upper_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Biceps Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 4, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
            ]},
            {"name": "Legs", "focus": "Lower Body", "day_type": None, "slots": [
                {"name": "Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Romanian Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Leg Press", "primary_muscle": "quads", "pattern": "squat", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Leg Curl", "primary_muscle": "hamstrings", "pattern": "knee_flexion", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Calf Raise", "primary_muscle": "calves", "pattern": "ankle_plantarflexion", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
            ]},
            {"name": "Upper", "focus": "Full Upper Body", "day_type": None, "slots": [
                {"name": "Incline Press", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Lat Pulldown", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "DB Shoulder Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Seated Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Arms Superset", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
            ]},
            {"name": "Lower", "focus": "Full Lower Body", "day_type": None, "slots": [
                {"name": "Front Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "core"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Hip Thrust", "primary_muscle": "glutes", "pattern": "hip_thrust", "category": "compound_primary", "sets": 4, "secondary_muscles": ["hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Walking Lunge", "primary_muscle": "quads", "pattern": "lunge", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Core", "primary_muscle": "abs", "pattern": "core_anti_extension", "category": "accessory", "sets": 3, "secondary_muscles": ["obliques"], "force_type_hint": None, "is_focus_emphasis": False},
            ]},
        ],
        "rest_days": [6, 7],
        "suitable_for_experience": ["intermediate", "advanced"],
        "suitable_for_goals": ["muscle_gain", "recomp", "strength"],
    },
    {
        "name": "body_part_split_5day",
        "split_type": "bodyPart",
        "days_per_week": 5,
        "description": "Five-day body-part split (bro split): one major muscle group per day. Classic hypertrophy focus.",
        "templates": [
            {"name": "Chest Day", "focus": "Chest", "day_type": None, "slots": [
                {"name": "Bench Press", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Incline DB Press", "primary_muscle": "chest", "pattern": "incline_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Cable Fly", "primary_muscle": "chest", "pattern": "chest_fly", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Dips", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Triceps Pushdown", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
            ]},
            {"name": "Back Day", "focus": "Back", "day_type": None, "slots": [
                {"name": "Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Pull-Up", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Barbell Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Lat Pulldown", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Biceps Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 4, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
            ]},
            {"name": "Shoulders Day", "focus": "Shoulders", "day_type": None, "slots": [
                {"name": "Overhead Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "DB Shoulder Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Lateral Raise", "primary_muscle": "shoulders", "pattern": "lateral_raise", "category": "accessory", "sets": 5, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Rear Delt Fly", "primary_muscle": "rear_delts", "pattern": "rear_delt", "category": "accessory", "sets": 4, "secondary_muscles": ["upper_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Shrug", "primary_muscle": "traps", "pattern": "shrug", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Pull", "is_focus_emphasis": False},
            ]},
            {"name": "Legs Day", "focus": "Quads/Hamstrings/Glutes", "day_type": None, "slots": [
                {"name": "Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Romanian Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Leg Press", "primary_muscle": "quads", "pattern": "squat", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Leg Curl", "primary_muscle": "hamstrings", "pattern": "knee_flexion", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Calf Raise", "primary_muscle": "calves", "pattern": "ankle_plantarflexion", "category": "accessory", "sets": 5, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
            ]},
            {"name": "Arms Day", "focus": "Biceps/Triceps", "day_type": None, "slots": [
                {"name": "Barbell Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 4, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Skull Crusher", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 4, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Hammer Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["forearms", "brachialis"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Triceps Pushdown", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Preacher Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
            ]},
        ],
        "rest_days": [6, 7],
        "suitable_for_experience": ["intermediate", "advanced"],
        "suitable_for_goals": ["muscle_gain", "maintenance"],
    },
    {
        "name": "push_pull_2day",
        "split_type": "pushPull",
        "days_per_week": 2,
        "description": "Two-day push/pull split for very low training frequency. Minimum effective dose.",
        "templates": [
            {"name": "Push Day", "focus": "Chest/Shoulders/Triceps/Quads", "day_type": None, "slots": [
                {"name": "Bench Press", "primary_muscle": "chest", "pattern": "horizontal_push", "category": "compound_primary", "sets": 4, "secondary_muscles": ["triceps", "shoulders"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Squat", "primary_muscle": "quads", "pattern": "squat", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "hamstrings"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Overhead Press", "primary_muscle": "shoulders", "pattern": "vertical_push", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["triceps"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Lunge", "primary_muscle": "quads", "pattern": "lunge", "category": "compound_secondary", "sets": 3, "secondary_muscles": ["glutes"], "force_type_hint": "Push", "is_focus_emphasis": False},
                {"name": "Triceps Extension", "primary_muscle": "triceps", "pattern": "elbow_extension", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Push", "is_focus_emphasis": False},
            ]},
            {"name": "Pull Day", "focus": "Back/Biceps/Hamstrings", "day_type": None, "slots": [
                {"name": "Deadlift", "primary_muscle": "hamstrings", "pattern": "hip_hinge", "category": "compound_primary", "sets": 4, "secondary_muscles": ["glutes", "lower_back", "traps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Pull-Up", "primary_muscle": "back", "pattern": "vertical_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Barbell Row", "primary_muscle": "back", "pattern": "horizontal_pull", "category": "compound_primary", "sets": 4, "secondary_muscles": ["biceps", "rear_delts"], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Leg Curl", "primary_muscle": "hamstrings", "pattern": "knee_flexion", "category": "accessory", "sets": 3, "secondary_muscles": [], "force_type_hint": "Pull", "is_focus_emphasis": False},
                {"name": "Biceps Curl", "primary_muscle": "biceps", "pattern": "elbow_flexion", "category": "accessory", "sets": 3, "secondary_muscles": ["forearms"], "force_type_hint": "Pull", "is_focus_emphasis": False},
            ]},
        ],
        "rest_days": [3, 4, 5, 6, 7],
        "suitable_for_experience": ["beginner", "novice", "intermediate"],
        "suitable_for_goals": ["general_fitness", "maintenance", "fat_loss"],
    },
]


# ============================================================
# 2. movement_patterns.json (40 patterns)
# ============================================================
def _pattern(family, primary, keywords, env_full, env_home, env_body):
    return {
        "family": family,
        "primary_muscles": primary,
        "detection_keywords": keywords,
        "env_preference": {
            "full_gym": env_full,
            "home_gym": env_home,
            "bodyweight_only": env_body,
        },
    }


MOVEMENT_PATTERNS = {
    # Push family
    "horizontal_push": _pattern("push", ["chest", "triceps", "shoulders"],
        ["bench", "press", "push-up", "pushup", "dip"],
        ["barbell", "dumbbell", "machine", "cable", "bodyweight", "kettlebell"],
        ["barbell", "dumbbell", "bodyweight", "kettlebell"],
        ["bodyweight", "bands"]),
    "incline_push": _pattern("push", ["chest", "shoulders", "triceps"],
        ["incline", "upper-chest"],
        ["barbell", "dumbbell", "machine", "cable"],
        ["barbell", "dumbbell"],
        ["bodyweight", "bands"]),
    "decline_push": _pattern("push", ["chest", "triceps"],
        ["decline"],
        ["barbell", "dumbbell", "machine"],
        ["barbell", "dumbbell"],
        ["bodyweight"]),
    "vertical_push": _pattern("push", ["shoulders", "triceps"],
        ["overhead-press", "military-press", "shoulder-press", "push-press", "arnold-press"],
        ["barbell", "dumbbell", "machine", "kettlebell", "cable"],
        ["barbell", "dumbbell", "kettlebell"],
        ["bodyweight", "bands"]),
    "lateral_raise": _pattern("push", ["shoulders", "side_delts"],
        ["lateral-raise", "side-raise", "lateral-fly"],
        ["dumbbell", "cable", "machine"],
        ["dumbbell", "bands"],
        ["bodyweight", "bands"]),
    "chest_fly": _pattern("push", ["chest"],
        ["fly", "pec-dec", "cable-crossover"],
        ["dumbbell", "cable", "machine"],
        ["dumbbell"],
        ["bodyweight", "bands"]),
    # Pull family
    "horizontal_pull": _pattern("pull", ["back", "lats", "biceps", "rear_delts"],
        ["row", "seated-row", "pendlay", "t-bar"],
        ["barbell", "dumbbell", "cable", "machine", "kettlebell"],
        ["barbell", "dumbbell", "kettlebell"],
        ["bodyweight", "bands"]),
    "vertical_pull": _pattern("pull", ["back", "lats", "biceps"],
        ["pull-up", "pulldown", "chin-up"],
        ["bodyweight", "cable", "machine"],
        ["bodyweight", "bands"],
        ["bodyweight", "bands"]),
    "rear_delt": _pattern("pull", ["rear_delts", "upper_back"],
        ["rear-delt", "face-pull", "reverse-fly"],
        ["dumbbell", "cable", "machine"],
        ["dumbbell", "bands"],
        ["bodyweight", "bands"]),
    "shrug": _pattern("pull", ["traps"],
        ["shrug", "trap"],
        ["barbell", "dumbbell", "machine", "cable"],
        ["barbell", "dumbbell", "kettlebell"],
        ["bodyweight"]),
    # Lower family
    "squat": _pattern("lower", ["quads", "glutes", "hamstrings"],
        ["squat", "hack-squat", "goblet-squat", "front-squat", "leg-press"],
        ["barbell", "dumbbell", "machine", "kettlebell", "bodyweight", "safety_bar", "trap_bar"],
        ["barbell", "dumbbell", "kettlebell", "bodyweight", "trap_bar"],
        ["bodyweight", "bands"]),
    "hip_hinge": _pattern("lower", ["hamstrings", "glutes", "lower_back"],
        ["deadlift", "rdl", "romanian", "good-morning", "hip-hinge"],
        ["barbell", "dumbbell", "kettlebell", "trap_bar", "machine"],
        ["barbell", "dumbbell", "kettlebell", "trap_bar"],
        ["bodyweight", "bands"]),
    "lunge": _pattern("lower", ["quads", "glutes", "hamstrings"],
        ["lunge", "split-squat", "step-up", "bulgarian"],
        ["barbell", "dumbbell", "kettlebell", "bodyweight"],
        ["barbell", "dumbbell", "kettlebell", "bodyweight"],
        ["bodyweight", "bands"]),
    "hip_thrust": _pattern("lower", ["glutes", "hamstrings"],
        ["hip-thrust", "glute-bridge"],
        ["barbell", "dumbbell", "machine", "kettlebell", "bodyweight"],
        ["barbell", "dumbbell", "kettlebell", "bodyweight"],
        ["bodyweight", "bands"]),
    "knee_extension": _pattern("lower", ["quads"],
        ["leg-extension", "knee-extension"],
        ["machine", "cable", "bands"],
        ["bands"],
        ["bands"]),
    "knee_flexion": _pattern("lower", ["hamstrings"],
        ["leg-curl", "hamstring-curl", "knee-flexion"],
        ["machine", "cable", "dumbbell"],
        ["dumbbell"],
        ["bodyweight", "bands"]),
    "ankle_plantarflexion": _pattern("lower", ["calves"],
        ["calf-raise", "plantarflexion", "seated-calf"],
        ["barbell", "dumbbell", "machine", "kettlebell", "bodyweight"],
        ["barbell", "dumbbell", "kettlebell", "bodyweight"],
        ["bodyweight", "bands"]),
    "glute_isolation": _pattern("lower", ["glutes"],
        ["kickback", "abduction", "glute-isolation"],
        ["cable", "machine", "dumbbell", "bands"],
        ["dumbbell", "bands"],
        ["bodyweight", "bands"]),
    # Arms family
    "elbow_flexion": _pattern("arms", ["biceps", "forearms"],
        ["curl", "preacher", "concentration", "hammer-curl"],
        ["barbell", "dumbbell", "cable", "machine", "ez_bar"],
        ["barbell", "dumbbell", "ez_bar"],
        ["bodyweight", "bands"]),
    "elbow_extension": _pattern("arms", ["triceps"],
        ["extension", "pushdown", "skull-crusher", "kickback", "french-press"],
        ["barbell", "dumbbell", "cable", "machine", "ez_bar"],
        ["barbell", "dumbbell", "ez_bar"],
        ["bodyweight", "bands"]),
    # Shoulders family
    "front_raise": _pattern("shoulders", ["shoulders"],
        ["front-raise"],
        ["dumbbell", "barbell", "cable", "kettlebell"],
        ["dumbbell", "barbell", "kettlebell"],
        ["bodyweight", "bands"]),
    # Core family
    "core_anti_extension": _pattern("core", ["abs"],
        ["plank", "ab-wheel", "rollout", "hanging-leg-raise"],
        ["bodyweight", "cable", "machine", "kettlebell"],
        ["bodyweight", "kettlebell"],
        ["bodyweight", "bands"]),
    "core_anti_rotation": _pattern("core", ["obliques", "abs"],
        ["pallof", "anti-rotation", "wood-chop", "russian-twist"],
        ["cable", "band", "dumbbell", "kettlebell"],
        ["dumbbell", "kettlebell", "bands"],
        ["bodyweight", "bands"]),
    "core_flexion": _pattern("core", ["abs"],
        ["crunch", "sit-up", "leg-raise", "v-up"],
        ["bodyweight", "cable", "machine"],
        ["bodyweight"],
        ["bodyweight"]),
    "core_rotation": _pattern("core", ["obliques"],
        ["russian-twist", "bicycle", "rotation", "cable-rotation"],
        ["cable", "dumbbell", "kettlebell", "bodyweight"],
        ["dumbbell", "kettlebell", "bodyweight"],
        ["bodyweight", "bands"]),
    # Mobility
    "mobility_hip": _pattern("mobility", ["glutes", "hip_flexors"],
        ["hip-mobility", "lunge-mobility", "spider"],
        ["bodyweight", "bands", "foam_roll"],
        ["bodyweight", "bands"],
        ["bodyweight", "bands"]),
    "mobility_thoracic": _pattern("mobility", ["upper_back", "lower_back"],
        ["thoracic", "cat-cow", "thread-the-needle"],
        ["bodyweight", "foam_roll"],
        ["bodyweight"],
        ["bodyweight"]),
    "mobility_ankle": _pattern("mobility", ["calves"],
        ["ankle-mobility", "ankle-circle"],
        ["bodyweight", "bands"],
        ["bodyweight", "bands"],
        ["bodyweight", "bands"]),
    "foam_roll": _pattern("mobility", ["quads", "hamstrings", "lats"],
        ["foam-roll", "smr", "self-myofascial"],
        ["foam_roll", "tiger_tail", "lacrosse_ball"],
        ["foam_roll"],
        []),
    # Cardio
    "cardio_steady": _pattern("cardio", [],
        ["run", "walk", "cycle", "row", "elliptical", "swim"],
        ["bodyweight", "machine", "jump_rope"],
        ["bodyweight", "jump_rope", "kettlebell"],
        ["bodyweight", "jump_rope"]),
    "cardio_hiit": _pattern("cardio", ["quads", "hamstrings", "glutes", "calves"],
        ["sprint", "burpee", "mountain-climber", "jumping-jack", "hiit"],
        ["bodyweight", "kettlebell", "jump_rope"],
        ["bodyweight", "kettlebell", "jump_rope"],
        ["bodyweight", "jump_rope", "bands"]),
    "plyometric": _pattern("cardio", ["quads", "glutes", "calves"],
        ["box-jump", "jump-squat", "depth-jump", "plyo"],
        ["bodyweight", "box"],
        ["bodyweight", "box"],
        ["bodyweight"]),
    # Compound carry
    "carry": _pattern("lower", ["core", "traps", "forearms", "glutes"],
        ["farmer-walk", "suitcase-carry", "carry", "rack-carry"],
        ["barbell", "dumbbell", "kettlebell", "trap_bar"],
        ["barbell", "dumbbell", "kettlebell", "trap_bar"],
        ["bodyweight", "bands"]),
    # Rotation/power
    "sprint": _pattern("cardio", ["hamstrings", "glutes", "calves"],
        ["sprint"],
        ["bodyweight"],
        ["bodyweight"],
        ["bodyweight"]),
    "row_cardio": _pattern("cardio", ["back", "lats", "biceps"],
        ["rowing", "erg"],
        ["machine"],
        [],
        []),
    # Other
    "forearm_flexion": _pattern("arms", ["forearms"],
        ["wrist-curl", "reverse-curl", "farmer-hold"],
        ["barbell", "dumbbell", "ez_bar"],
        ["barbell", "dumbbell", "ez_bar"],
        ["bodyweight"]),
    "neck": _pattern("shoulders", ["traps"],
        ["neck-flexion", "neck-extension", "neck-bridge"],
        ["bodyweight", "machine"],
        ["bodyweight"],
        ["bodyweight"]),
    "adduction": _pattern("lower", ["adductors"],
        ["adduction", "adductor", "copenhagen"],
        ["machine", "cable", "bodyweight"],
        ["bodyweight"],
        ["bodyweight", "bands"]),
    "abduction": _pattern("lower", ["abductors", "glutes"],
        ["abduction", "abductor", "banded-walk"],
        ["machine", "cable", "bands"],
        ["bands"],
        ["bodyweight", "bands"]),
}


# ============================================================
# 3. food_database.json (filler foods)
# ============================================================
def _food(slug, name, category, serving_g, per100):
    return {
        "slug": slug,
        "name": name,
        "category": category,
        "serving_g": serving_g,
        "per_100g": per100,
    }


FOOD_DATABASE = {
    # Animal proteins (OMNI)
    "whey": _food("whey", "Whey Protein Powder", "proteinAnimal", 30, {"kcal": 400, "protein_g": 80, "carb_g": 10, "fat_g": 6, "fiber_g": 0}),
    "greek_yogurt": _food("greek_yogurt", "Greek Yogurt (plain, nonfat)", "dairy", 170, {"kcal": 60, "protein_g": 10, "carb_g": 4, "fat_g": 0, "fiber_g": 0}),
    "egg_white": _food("egg_white", "Egg Whites", "proteinAnimal", 100, {"kcal": 52, "protein_g": 11, "carb_g": 1, "fat_g": 0, "fiber_g": 0}),
    "cottage_cheese": _food("cottage_cheese", "Cottage Cheese (lowfat)", "dairy", 226, {"kcal": 90, "protein_g": 12, "carb_g": 6, "fat_g": 2, "fiber_g": 0}),
    "chicken_breast": _food("chicken_breast", "Chicken Breast (cooked)", "proteinAnimal", 100, {"kcal": 165, "protein_g": 31, "carb_g": 0, "fat_g": 3.6, "fiber_g": 0}),
    "milk": _food("milk", "Milk (2%)", "dairy", 240, {"kcal": 122, "protein_g": 8, "carb_g": 12, "fat_g": 5, "fiber_g": 0}),
    "cheddar": _food("cheddar", "Cheddar Cheese", "dairy", 30, {"kcal": 121, "protein_g": 7, "carb_g": 0, "fat_g": 10, "fiber_g": 0}),
    # Plant proteins (VEGAN)
    "tofu": _food("tofu", "Tofu (firm)", "proteinPlant", 100, {"kcal": 144, "protein_g": 17, "carb_g": 3, "fat_g": 9, "fiber_g": 2}),
    "tempeh": _food("tempeh", "Tempeh", "proteinPlant", 100, {"kcal": 192, "protein_g": 20, "carb_g": 8, "fat_g": 11, "fiber_g": 0}),
    "pea_protein": _food("pea_protein", "Pea Protein Powder", "proteinPlant", 30, {"kcal": 420, "protein_g": 80, "carb_g": 8, "fat_g": 7, "fiber_g": 0}),
    "soy_protein": _food("soy_protein", "Soy Protein Isolate", "proteinPlant", 30, {"kcal": 410, "protein_g": 90, "carb_g": 0, "fat_g": 4, "fiber_g": 0}),
    "lentils": _food("lentils", "Lentils (cooked)", "proteinPlant", 100, {"kcal": 116, "protein_g": 9, "carb_g": 20, "fat_g": 0.4, "fiber_g": 8}),
    # Carbs
    "white_rice": _food("white_rice", "White Rice (cooked)", "carbGrain", 100, {"kcal": 130, "protein_g": 2.7, "carb_g": 28, "fat_g": 0.3, "fiber_g": 0.4}),
    "brown_rice": _food("brown_rice", "Brown Rice (cooked)", "carbGrain", 100, {"kcal": 123, "protein_g": 2.7, "carb_g": 26, "fat_g": 1, "fiber_g": 1.8}),
    "oats": _food("oats", "Rolled Oats (dry)", "carbGrain", 40, {"kcal": 389, "protein_g": 17, "carb_g": 66, "fat_g": 7, "fiber_g": 10}),
    "banana": _food("banana", "Banana", "carbFruit", 118, {"kcal": 89, "protein_g": 1.1, "carb_g": 23, "fat_g": 0.3, "fiber_g": 2.6}),
    "whole_wheat_bread": _food("whole_wheat_bread", "Whole Wheat Bread", "carbGrain", 28, {"kcal": 247, "protein_g": 13, "carb_g": 41, "fat_g": 4.2, "fiber_g": 7}),
    "quinoa": _food("quinoa", "Quinoa (cooked)", "carbGrain", 100, {"kcal": 120, "protein_g": 4.4, "carb_g": 21, "fat_g": 1.9, "fiber_g": 2.8}),
    "sweet_potato": _food("sweet_potato", "Sweet Potato (baked)", "carbStarchyVeg", 100, {"kcal": 90, "protein_g": 2, "carb_g": 21, "fat_g": 0.1, "fiber_g": 3.3}),
    # Fats
    "olive_oil": _food("olive_oil", "Olive Oil", "fatOil", 14, {"kcal": 884, "protein_g": 0, "carb_g": 0, "fat_g": 100, "fiber_g": 0}),
    "almonds": _food("almonds", "Almonds", "fatNutSeed", 28, {"kcal": 579, "protein_g": 21, "carb_g": 22, "fat_g": 50, "fiber_g": 12}),
    "peanut_butter": _food("peanut_butter", "Peanut Butter", "fatNutSeed", 32, {"kcal": 588, "protein_g": 25, "carb_g": 20, "fat_g": 50, "fiber_g": 6}),
    "walnuts": _food("walnuts", "Walnuts", "fatNutSeed", 28, {"kcal": 654, "protein_g": 15, "carb_g": 14, "fat_g": 65, "fiber_g": 6.7}),
    "avocado": _food("avocado", "Avocado", "fatOil", 100, {"kcal": 160, "protein_g": 2, "carb_g": 9, "fat_g": 15, "fiber_g": 7}),
    # Vegetables
    "broccoli": _food("broccoli", "Broccoli (steamed)", "vegetable", 100, {"kcal": 35, "protein_g": 2.4, "carb_g": 7, "fat_g": 0.4, "fiber_g": 3.3}),
    "spinach": _food("spinach", "Spinach (cooked)", "vegetable", 100, {"kcal": 23, "protein_g": 3, "carb_g": 4, "fat_g": 0.3, "fiber_g": 2.4}),
    "mixed_greens": _food("mixed_greens", "Mixed Greens", "vegetable", 100, {"kcal": 20, "protein_g": 2, "carb_g": 3, "fat_g": 0.3, "fiber_g": 2}),
    "bell_pepper": _food("bell_pepper", "Bell Pepper", "vegetable", 100, {"kcal": 31, "protein_g": 1, "carb_g": 6, "fat_g": 0.3, "fiber_g": 2.1}),
    "asparagus": _food("asparagus", "Asparagus", "vegetable", 100, {"kcal": 20, "protein_g": 2.2, "carb_g": 3.9, "fat_g": 0.1, "fiber_g": 2.1}),
    "green_beans": _food("green_beans", "Green Beans", "vegetable", 100, {"kcal": 35, "protein_g": 1.8, "carb_g": 7, "fat_g": 0.5, "fiber_g": 3.4}),
    "carrots": _food("carrots", "Carrots", "vegetable", 100, {"kcal": 41, "protein_g": 0.9, "carb_g": 10, "fat_g": 0.2, "fiber_g": 2.8}),
}


# ============================================================
# 4. pre_post_workout_recipes.json (16 entries)
# ============================================================
def _pw(id_, diet, meal_type, name, ingredients, instructions, nutrition):
    return {
        "id": id_,
        "name": name,
        "source": "engine-generated",
        "cuisine": "neutral",
        "meal_types": [meal_type],
        "diet_types": [diet],
        "servings": 1,
        "prep_time_min": 5,
        "cook_time_min": 0,
        "ingredients": ingredients,
        "instructions": instructions,
        "nutrition_per_serving": nutrition,
        "nutrition_source": "calculated",
        "protein_density": "high" if nutrition["protein_g"] >= 25 else ("medium" if nutrition["protein_g"] >= 15 else "low"),
        "calorie_density": "low" if nutrition["kcal"] < 200 else ("medium" if nutrition["kcal"] < 400 else "high"),
        "allergens": [],
        "goal_fit": ["bulk", "maintenance", "recomp", "strength"],
        "image_url": "",
        "alternative_recipe_ids": [],
        "fasting_yetsom": False,
        "injera_accompaniment": False,
        "notes": " [pre/post workout — engine-generated]",
    }


PRE_POST = []
DIETS = ["OMNI", "VEGAN", "OMNI_ETHIOPIAN", "VEGAN_ETHIOPIAN"]
for diet in DIETS:
    PRE_POST.append(_pw(
        f"PW-{diet}-pre-low", diet, "pre_workout",
        f"Pre-Workout Banana Oats ({diet})",
        ["1 medium banana (118g)", "30g rolled oats", "150ml almond milk" if "VEGAN" in diet else "150ml skim milk"],
        ["Combine oats and milk; microwave 90 seconds.", "Top with sliced banana.", "Eat 30-45 min before training."],
        {"kcal": 180, "protein_g": 5, "carb_g": 35, "fat_g": 2, "fiber_g": 4, "sugar_g": 12},
    ))
    PRE_POST.append(_pw(
        f"PW-{diet}-pre-high", diet, "pre_workout",
        f"Pre-Workout Oat Energy Bowl ({diet})",
        ["60g rolled oats", "1 banana", "15g almond butter" if "VEGAN" in diet else "15g peanut butter", "200ml almond milk" if "VEGAN" in diet else "200ml milk", "1 tsp honey"],
        ["Combine oats and milk; microwave 90 seconds.", "Stir in nut butter.", "Top with banana slices and honey."],
        {"kcal": 320, "protein_g": 9, "carb_g": 55, "fat_g": 9, "fiber_g": 6, "sugar_g": 22},
    ))
    if "VEGAN" not in diet:
        PRE_POST.append(_pw(
            f"PW-{diet}-post-low", diet, "post_workout",
            f"Post-Workout Greek Yogurt Bowl ({diet})",
            ["200g nonfat Greek yogurt", "1 medium banana", "15g honey", "30g rolled oats"],
            ["Combine yogurt and oats.", "Top with banana slices.", "Drizzle honey on top."],
            {"kcal": 270, "protein_g": 25, "carb_g": 40, "fat_g": 2, "fiber_g": 4, "sugar_g": 25},
        ))
    else:
        PRE_POST.append(_pw(
            f"PW-{diet}-post-low", diet, "post_workout",
            f"Post-Workout Soy Protein Shake ({diet})",
            ["30g soy protein isolate", "1 medium banana", "250ml almond milk", "5g cocoa powder"],
            ["Blend all ingredients until smooth.", "Drink within 30 min after training."],
            {"kcal": 270, "protein_g": 27, "carb_g": 30, "fat_g": 4, "fiber_g": 4, "sugar_g": 16},
        ))
    if "VEGAN" not in diet:
        PRE_POST.append(_pw(
            f"PW-{diet}-post-high", diet, "post_workout",
            f"Post-Workout Recovery Smoothie ({diet})",
            ["200g nonfat Greek yogurt", "1 banana", "200ml milk", "30g whey protein", "15g peanut butter", "1 cup ice"],
            ["Blend all ingredients until smooth.", "Consume within 30 min post-workout."],
            {"kcal": 450, "protein_g": 50, "carb_g": 45, "fat_g": 10, "fiber_g": 5, "sugar_g": 30},
        ))
    else:
        PRE_POST.append(_pw(
            f"PW-{diet}-post-high", diet, "post_workout",
            f"Post-Workout Vegan Recovery Smoothie ({diet})",
            ["30g pea protein", "1 banana", "200ml almond milk", "20g peanut butter", "30g oats", "1 cup ice"],
            ["Blend all ingredients until smooth.", "Consume within 30 min post-workout."],
            {"kcal": 450, "protein_g": 35, "carb_g": 50, "fat_g": 13, "fiber_g": 8, "sugar_g": 18},
        ))


# ============================================================
# 5. recipe_database.json (small curated subset)
# ============================================================
CURATED = [
    {
        "id": "R001", "name": "Alicha Doro Wot", "source": "https://example.com/alicha-doro-wot",
        "cuisine": "ethiopian", "meal_types": ["dinner", "lunch"],
        "diet_types": ["OMNI_ETHIOPIAN"], "goal_fit": ["bulk", "maintenance"],
        "servings": 5, "prep_time_min": 30, "cook_time_min": 60,
        "ingredients": ["3 pounds chicken thighs", "4 hard-boiled eggs", "2 large onions (diced)", "3 tbsp niter kibbeh", "2 tbsp garlic-ginger paste", "1 tsp turmeric", "Salt to taste"],
        "instructions": ["Sauté onions in niter kibbeh until golden.", "Add garlic-ginger paste and turmeric.", "Add chicken and brown lightly.", "Cover and simmer 45 minutes.", "Add hard-boiled eggs in the last 10 minutes.", "Serve with injera."],
        "nutrition_per_serving": {"kcal": 520.0, "protein_g": 38.0, "carb_g": 12.0, "fat_g": 34.0, "fiber_g": 2.0, "sugar_g": 4.0},
        "nutrition_source": "published", "protein_density": "high", "calorie_density": "high",
        "allergens": ["eggs"], "fasting_yetsom": False, "injera_accompaniment": True,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Ethiopian cuisine; high protein; great for bulking",
        "top_alternatives": [],
    },
    {
        "id": "R002", "name": "Misir Wot (Spiced Red Lentils)", "source": "https://example.com/misir-wot",
        "cuisine": "ethiopian", "meal_types": ["dinner", "lunch"],
        "diet_types": ["VEGAN_ETHIOPIAN"], "goal_fit": ["bulk", "maintenance", "recomp"],
        "servings": 4, "prep_time_min": 10, "cook_time_min": 30,
        "ingredients": ["1 cup red lentils", "1 large onion (diced)", "2 tbsp olive oil", "2 tbsp berbere spice", "1 tbsp garlic-ginger paste", "3 cups water"],
        "instructions": ["Sauté onion in oil until soft.", "Add berbere and garlic-ginger paste; toast 1 min.", "Add lentils and water; bring to boil.", "Simmer 20-25 min until lentils break down.", "Season and serve with injera."],
        "nutrition_per_serving": {"kcal": 320.0, "protein_g": 14.0, "carb_g": 42.0, "fat_g": 10.0, "fiber_g": 12.0, "sugar_g": 4.0},
        "nutrition_source": "published", "protein_density": "medium", "calorie_density": "medium",
        "allergens": [], "fasting_yetsom": True, "injera_accompaniment": True,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Vegan Ethiopian; high fiber; plant protein",
        "top_alternatives": [],
    },
    {
        "id": "R003", "name": "Greek Yogurt Parfait", "source": "https://example.com/yogurt-parfait",
        "cuisine": "american", "meal_types": ["breakfast", "snack"],
        "diet_types": ["OMNI"], "goal_fit": ["recomp", "maintenance", "fat_loss"],
        "servings": 1, "prep_time_min": 5, "cook_time_min": 0,
        "ingredients": ["200g nonfat Greek yogurt", "30g rolled oats", "100g mixed berries", "15g honey", "10g almonds (chopped)"],
        "instructions": ["Layer yogurt and oats in a glass.", "Top with berries.", "Drizzle honey and sprinkle almonds."],
        "nutrition_per_serving": {"kcal": 380.0, "protein_g": 25.0, "carb_g": 50.0, "fat_g": 9.0, "fiber_g": 7.0, "sugar_g": 28.0},
        "nutrition_source": "calculated", "protein_density": "high", "calorie_density": "medium",
        "allergens": ["dairy", "nuts"], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Quick breakfast; high protein; balanced macros",
        "top_alternatives": [],
    },
    {
        "id": "R004", "name": "Oatmeal Power Bowl", "source": "https://example.com/oatmeal-bowl",
        "cuisine": "american", "meal_types": ["breakfast"],
        "diet_types": ["VEGAN"], "goal_fit": ["bulk", "maintenance"],
        "servings": 1, "prep_time_min": 5, "cook_time_min": 5,
        "ingredients": ["60g rolled oats", "250ml almond milk", "1 banana (sliced)", "20g peanut butter", "10g chia seeds", "5g cinnamon"],
        "instructions": ["Combine oats and almond milk; microwave 90 seconds.", "Stir, then top with banana, peanut butter, chia, and cinnamon."],
        "nutrition_per_serving": {"kcal": 510.0, "protein_g": 14.0, "carb_g": 75.0, "fat_g": 17.0, "fiber_g": 12.0, "sugar_g": 25.0},
        "nutrition_source": "calculated", "protein_density": "medium", "calorie_density": "high",
        "allergens": ["peanuts"], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Vegan breakfast; high fiber; calorie-dense for bulking",
        "top_alternatives": [],
    },
    {
        "id": "R005", "name": "Egg & Avocado Toast", "source": "https://example.com/egg-avocado-toast",
        "cuisine": "american", "meal_types": ["breakfast", "lunch"],
        "diet_types": ["OMNI"], "goal_fit": ["recomp", "maintenance"],
        "servings": 1, "prep_time_min": 10, "cook_time_min": 5,
        "ingredients": ["2 slices whole wheat bread", "2 eggs", "1/2 avocado", "Salt, pepper, chili flakes"],
        "instructions": ["Toast bread.", "Fry eggs sunny-side up.", "Mash avocado on toast; top with eggs; season."],
        "nutrition_per_serving": {"kcal": 460.0, "protein_g": 22.0, "carb_g": 36.0, "fat_g": 24.0, "fiber_g": 10.0, "sugar_g": 4.0},
        "nutrition_source": "calculated", "protein_density": "high", "calorie_density": "medium",
        "allergens": ["eggs", "gluten"], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Balanced breakfast; healthy fats; satiating",
        "top_alternatives": [],
    },
    {
        "id": "R006", "name": "Grilled Chicken & Quinoa Bowl", "source": "https://example.com/chicken-quinoa-bowl",
        "cuisine": "mediterranean", "meal_types": ["lunch", "dinner"],
        "diet_types": ["OMNI"], "goal_fit": ["recomp", "maintenance", "fat_loss"],
        "servings": 1, "prep_time_min": 15, "cook_time_min": 20,
        "ingredients": ["150g chicken breast", "80g dry quinoa", "100g mixed greens", "1/2 cucumber (sliced)", "5 cherry tomatoes", "1 tbsp olive oil", "Lemon juice"],
        "instructions": ["Cook quinoa per package.", "Grill chicken 5 min/side; slice.", "Combine quinoa, greens, vegetables; top with chicken.", "Dress with olive oil and lemon."],
        "nutrition_per_serving": {"kcal": 540.0, "protein_g": 45.0, "carb_g": 50.0, "fat_g": 17.0, "fiber_g": 7.0, "sugar_g": 4.0},
        "nutrition_source": "calculated", "protein_density": "high", "calorie_density": "medium",
        "allergens": [], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "High protein; balanced; lean bulk favorite",
        "top_alternatives": [],
    },
    {
        "id": "R007", "name": "Tofu Stir-Fry with Brown Rice", "source": "https://example.com/tofu-stirfry",
        "cuisine": "asian", "meal_types": ["dinner", "lunch"],
        "diet_types": ["VEGAN"], "goal_fit": ["recomp", "maintenance", "fat_loss"],
        "servings": 2, "prep_time_min": 15, "cook_time_min": 15,
        "ingredients": ["300g firm tofu (cubed)", "150g broccoli florets", "1 red bell pepper (sliced)", "100g brown rice (dry)", "2 tbsp soy sauce", "1 tbsp sesame oil", "1 tbsp ginger-garlic paste"],
        "instructions": ["Cook rice per package.", "Pan-fry tofu in sesame oil until golden.", "Add vegetables and ginger-garlic; stir-fry 5 min.", "Add soy sauce; serve over rice."],
        "nutrition_per_serving": {"kcal": 480.0, "protein_g": 24.0, "carb_g": 55.0, "fat_g": 16.0, "fiber_g": 6.0, "sugar_g": 4.0},
        "nutrition_source": "calculated", "protein_density": "high", "calorie_density": "medium",
        "allergens": ["soy"], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Vegan; balanced; high plant protein",
        "top_alternatives": [],
    },
    {
        "id": "R008", "name": "Salmon with Sweet Potato & Asparagus", "source": "https://example.com/salmon-sweet-potato",
        "cuisine": "mediterranean", "meal_types": ["dinner"],
        "diet_types": ["OMNI"], "goal_fit": ["recomp", "maintenance", "fat_loss"],
        "servings": 1, "prep_time_min": 10, "cook_time_min": 25,
        "ingredients": ["150g salmon fillet", "200g sweet potato (cubed)", "150g asparagus", "1 tbsp olive oil", "Lemon, salt, pepper"],
        "instructions": ["Roast sweet potato at 220C for 20 min.", "Add asparagus for last 10 min.", "Pan-sear salmon skin-side down 4 min; flip 2 min.", "Serve with lemon."],
        "nutrition_per_serving": {"kcal": 580.0, "protein_g": 38.0, "carb_g": 40.0, "fat_g": 28.0, "fiber_g": 7.0, "sugar_g": 10.0},
        "nutrition_source": "calculated", "protein_density": "high", "calorie_density": "medium",
        "allergens": ["fish"], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Omega-3 rich; high protein; nutrient-dense",
        "top_alternatives": [],
    },
    {
        "id": "R009", "name": "Shiro Wot (Chickpea Flour Stew)", "source": "https://example.com/shiro-wot",
        "cuisine": "ethiopian", "meal_types": ["dinner", "lunch"],
        "diet_types": ["VEGAN_ETHIOPIAN"], "goal_fit": ["bulk", "maintenance"],
        "servings": 4, "prep_time_min": 10, "cook_time_min": 25,
        "ingredients": ["1 cup shiro powder", "1 large onion (diced)", "3 tbsp olive oil", "2 tbsp garlic-ginger paste", "4 cups water", "Salt, berbere to taste"],
        "instructions": ["Sauté onion in oil until golden.", "Add garlic-ginger paste.", "Whisk shiro into water; add to pot.", "Simmer 15-20 min until thick.", "Serve with injera."],
        "nutrition_per_serving": {"kcal": 380.0, "protein_g": 12.0, "carb_g": 38.0, "fat_g": 18.0, "fiber_g": 6.0, "sugar_g": 3.0},
        "nutrition_source": "published", "protein_density": "medium", "calorie_density": "medium",
        "allergens": [], "fasting_yetsom": True, "injera_accompaniment": True,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Vegan Ethiopian; comfort food; fasting-friendly",
        "top_alternatives": [],
    },
    {
        "id": "R010", "name": "Cottage Cheese & Berry Bowl", "source": "https://example.com/cottage-berry",
        "cuisine": "american", "meal_types": ["snack", "breakfast"],
        "diet_types": ["OMNI"], "goal_fit": ["fat_loss", "recomp"],
        "servings": 1, "prep_time_min": 5, "cook_time_min": 0,
        "ingredients": ["200g lowfat cottage cheese", "100g mixed berries", "10g chia seeds", "5g stevia or honey"],
        "instructions": ["Combine cottage cheese and berries in bowl.", "Sprinkle chia and sweetener."],
        "nutrition_per_serving": {"kcal": 230.0, "protein_g": 28.0, "carb_g": 18.0, "fat_g": 5.0, "fiber_g": 6.0, "sugar_g": 12.0},
        "nutrition_source": "calculated", "protein_density": "high", "calorie_density": "low",
        "allergens": ["dairy"], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "High-protein snack; casein for slow release",
        "top_alternatives": [],
    },
    {
        "id": "R011", "name": "Lentil & Vegetable Soup", "source": "https://example.com/lentil-soup",
        "cuisine": "mediterranean", "meal_types": ["lunch", "dinner"],
        "diet_types": ["VEGAN"], "goal_fit": ["fat_loss", "recomp", "maintenance"],
        "servings": 4, "prep_time_min": 15, "cook_time_min": 35,
        "ingredients": ["1 cup brown lentils", "1 onion (diced)", "2 carrots (chopped)", "2 celery stalks", "2 garlic cloves", "1 can diced tomatoes", "6 cups vegetable broth", "1 tsp cumin", "1 tsp smoked paprika"],
        "instructions": ["Sauté onion, carrots, celery 5 min.", "Add garlic and spices.", "Add lentils, tomatoes, broth; boil.", "Simmer 30 min until lentils are tender."],
        "nutrition_per_serving": {"kcal": 280.0, "protein_g": 16.0, "carb_g": 45.0, "fat_g": 3.0, "fiber_g": 12.0, "sugar_g": 6.0},
        "nutrition_source": "calculated", "protein_density": "medium", "calorie_density": "low",
        "allergens": [], "fasting_yetsom": True, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Vegan; high fiber; low calorie; satiating",
        "top_alternatives": [],
    },
    {
        "id": "R012", "name": "Beef Stir-Fry with Vegetables", "source": "https://example.com/beef-stirfry",
        "cuisine": "asian", "meal_types": ["dinner", "lunch"],
        "diet_types": ["OMNI"], "goal_fit": ["bulk", "maintenance"],
        "servings": 2, "prep_time_min": 15, "cook_time_min": 15,
        "ingredients": ["300g lean beef strips", "150g broccoli", "1 bell pepper (sliced)", "100g white rice (dry)", "2 tbsp soy sauce", "1 tbsp sesame oil", "1 tbsp ginger-garlic paste", "1 tsp cornstarch"],
        "instructions": ["Cook rice.", "Sear beef in sesame oil; remove.", "Stir-fry vegetables 3 min.", "Return beef; add soy+cornstarch slurry.", "Serve over rice."],
        "nutrition_per_serving": {"kcal": 620.0, "protein_g": 42.0, "carb_g": 60.0, "fat_g": 20.0, "fiber_g": 5.0, "sugar_g": 4.0},
        "nutrition_source": "calculated", "protein_density": "high", "calorie_density": "high",
        "allergens": ["soy"], "fasting_yetsom": False, "injera_accompaniment": False,
        "image_url": "", "alternative_recipe_ids": [], "notes": " [curated]",
        "selection_reason": "Calorie-dense; high protein; great for bulking",
        "top_alternatives": [],
    },
]


# ============================================================
# Write all files
# ============================================================
def write(name, payload):
    path = os.path.join(ASSETS, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"wrote {path}: {os.path.getsize(path)} bytes")


write("split_designs.json", SPLIT_DESIGNS)
write("movement_patterns.json", MOVEMENT_PATTERNS)
write("food_database.json", FOOD_DATABASE)
write("pre_post_workout_recipes.json", {"version": "3.2.0", "total_recipes": len(PRE_POST), "recipes": PRE_POST})
write("recipe_database.json", {"version": "3.2.0", "total_recipes": len(CURATED), "recipes": CURATED, "swap_groups": {}})

print("\nAll data files generated.")
