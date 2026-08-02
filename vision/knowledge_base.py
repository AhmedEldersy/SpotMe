from typing import Any, Dict, List, Optional

SUPPORTED_SPORTS = ["Football", "Basketball", "Volleyball", "Handball"]

AGE_GROUPS = ["U13", "U15", "U17", "U19", "Senior"]

COMPETITION_LEVELS = ["Grassroots", "Academy", "Semi-Pro", "Professional", "Elite/National"]

CLASSIFICATION_LEVELS = [
    "Very Poor", "Poor", "Below Average", "Average", "Good", "Excellent", "Elite",
]

KB_VERSION = "1.0.0"

KB_DISCLAIMER = (
    "Reference bands and exercises come from an internal sports-science knowledge base "
    "(v" + KB_VERSION + "), compiled as literature-informed baselines for team-sport athletes. "
    "They are general starting points, not certified federation lab norms. When the exact "
    "sport, position, age group, or competition level is not covered, the closest available "
    "reference was used and this must be disclosed as an approximation, never presented as an "
    "exact match."
)


BENCHMARKS: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]] = {
    "Football": {
        "U17": {
            "Academy": {
                "top_speed_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [5.5, 6.0, 6.4, 6.8, 7.2, 7.6]},
                "speed_avg_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [1.5, 1.8, 2.0, 2.3, 2.6, 2.9]},
                "sprint_count": {"unit": "sprints/session", "direction": "higher_better",
                                   "bands": [3, 5, 7, 9, 12, 15]},
                "distance_covered_m": {"unit": "m", "direction": "higher_better",
                                         "bands": [2500, 3500, 4500, 5500, 6500, 7500]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.05, 0.10, 0.15, 0.22, 0.30, 0.40]},
                "movement_efficiency": {"unit": "0-1", "direction": "higher_better",
                                          "bands": [0.15, 0.25, 0.35, 0.45, 0.55, 0.65]},
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [20, 25, 29, 33, 37, 42]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.4, 0.55, 0.65, 0.75, 0.85, 0.92]},
                "balance": {"unit": "0-1", "direction": "higher_better",
                             "bands": [0.4, 0.55, 0.65, 0.75, 0.85, 0.92]},
            },
        },
        "Senior": {
            "Professional": {
                "top_speed_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [6.5, 7.0, 7.5, 8.0, 8.5, 9.0]},
                "speed_avg_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [1.8, 2.1, 2.4, 2.7, 3.0, 3.3]},
                "sprint_count": {"unit": "sprints/session", "direction": "higher_better",
                                   "bands": [5, 8, 11, 14, 18, 22]},
                "distance_covered_m": {"unit": "m", "direction": "higher_better",
                                         "bands": [4000, 5500, 7000, 8500, 10000, 11500]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.04, 0.08, 0.12, 0.18, 0.25, 0.35]},
                "movement_efficiency": {"unit": "0-1", "direction": "higher_better",
                                          "bands": [0.18, 0.28, 0.38, 0.48, 0.58, 0.68]},
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [28, 33, 37, 41, 46, 52]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.5, 0.62, 0.72, 0.8, 0.88, 0.94]},
                "balance": {"unit": "0-1", "direction": "higher_better",
                             "bands": [0.5, 0.62, 0.72, 0.8, 0.88, 0.94]},
            },
        },
    },
    "Basketball": {
        "U17": {
            "Academy": {
                "top_speed_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [4.8, 5.2, 5.6, 6.0, 6.4, 6.8]},
                "sprint_count": {"unit": "sprints/session", "direction": "higher_better",
                                   "bands": [3, 5, 7, 9, 12, 15]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.05, 0.10, 0.16, 0.23, 0.31, 0.40]},
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [28, 33, 37, 42, 47, 53]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.4, 0.55, 0.65, 0.75, 0.85, 0.92]},
                "balance": {"unit": "0-1", "direction": "higher_better",
                             "bands": [0.4, 0.55, 0.65, 0.75, 0.85, 0.92]},
            },
        },
        "Senior": {
            "Professional": {
                "top_speed_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [5.5, 6.0, 6.4, 6.8, 7.2, 7.6]},
                "sprint_count": {"unit": "sprints/session", "direction": "higher_better",
                                   "bands": [4, 7, 10, 13, 17, 21]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.04, 0.08, 0.13, 0.19, 0.26, 0.35]},
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [38, 44, 49, 55, 61, 68]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.5, 0.62, 0.72, 0.8, 0.88, 0.94]},
                "balance": {"unit": "0-1", "direction": "higher_better",
                             "bands": [0.5, 0.62, 0.72, 0.8, 0.88, 0.94]},
            },
        },
    },
    "Volleyball": {
        "U17": {
            "Academy": {
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [26, 31, 35, 40, 45, 51]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.4, 0.55, 0.65, 0.75, 0.85, 0.92]},
                "balance": {"unit": "0-1", "direction": "higher_better",
                             "bands": [0.4, 0.55, 0.65, 0.75, 0.85, 0.92]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.05, 0.10, 0.16, 0.23, 0.31, 0.40]},
            },
        },
        "Senior": {
            "Professional": {
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [40, 46, 52, 58, 65, 72]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.5, 0.62, 0.72, 0.8, 0.88, 0.94]},
                "balance": {"unit": "0-1", "direction": "higher_better",
                             "bands": [0.5, 0.62, 0.72, 0.8, 0.88, 0.94]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.04, 0.08, 0.13, 0.19, 0.26, 0.35]},
            },
        },
    },
    "Handball": {
        "U17": {
            "Academy": {
                "top_speed_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [5.0, 5.4, 5.8, 6.2, 6.6, 7.0]},
                "sprint_count": {"unit": "sprints/session", "direction": "higher_better",
                                   "bands": [3, 5, 7, 9, 12, 15]},
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [24, 29, 33, 37, 42, 47]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.4, 0.55, 0.65, 0.75, 0.85, 0.92]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.05, 0.10, 0.16, 0.23, 0.31, 0.40]},
            },
        },
        "Senior": {
            "Professional": {
                "top_speed_ms": {"unit": "m/s", "direction": "higher_better",
                                  "bands": [5.8, 6.3, 6.7, 7.1, 7.5, 8.0]},
                "sprint_count": {"unit": "sprints/session", "direction": "higher_better",
                                   "bands": [5, 8, 11, 14, 18, 22]},
                "jump_height_cm": {"unit": "cm", "direction": "higher_better",
                                     "bands": [34, 40, 45, 50, 56, 63]},
                "landing_stability": {"unit": "0-1", "direction": "higher_better",
                                        "bands": [0.5, 0.62, 0.72, 0.8, 0.88, 0.94]},
                "fatigue_index": {"unit": "0-1 (drop-off)", "direction": "lower_better",
                                    "bands": [0.04, 0.08, 0.13, 0.19, 0.26, 0.35]},
            },
        },
    },
}


_AGE_ORDER = ["U13", "U15", "U17", "U19", "Senior"]
_LEVEL_ORDER = ["Grassroots", "Academy", "Semi-Pro", "Professional", "Elite/National"]


def _closest(value: str, options: List[str], order: List[str]) -> str:
    if value in options:
        return value
    if value not in order:
        return options[0]
    target_idx = order.index(value)
    best = min(
        options,
        key=lambda o: abs(order.index(o) - target_idx) if o in order else 999,
    )
    return best


def classify_metric(value: Optional[float], spec: Dict[str, Any]) -> str:
    """Classify a raw metric value into one of CLASSIFICATION_LEVELS using
    the metric's band spec. Returns 'Unknown' if value is None (never guess)."""
    if value is None:
        return "Unknown"
    bands = spec["bands"]
    direction = spec.get("direction", "higher_better")
    if direction == "higher_better":
        for i, boundary in enumerate(bands):
            if value < boundary:
                return CLASSIFICATION_LEVELS[i]
        return CLASSIFICATION_LEVELS[-1]
    else:  # lower_better
        reversed_labels = list(reversed(CLASSIFICATION_LEVELS))
        for i, boundary in enumerate(bands):
            if value <= boundary:
                return reversed_labels[i]
        return reversed_labels[-1]


def get_benchmark_bands(sport: str, age_group: Optional[str], competition_level: Optional[str]):
    """Return (bands_dict, resolved_age_group, resolved_level, was_exact_match)."""
    sport_data = BENCHMARKS.get(sport)
    if not sport_data:
        return {}, age_group, competition_level, False

    available_ages = list(sport_data.keys())
    resolved_age = _closest(age_group or "Senior", available_ages, _AGE_ORDER)

    age_data = sport_data[resolved_age]
    available_levels = list(age_data.keys())
    resolved_level = _closest(competition_level or "Professional", available_levels, _LEVEL_ORDER)

    exact = (resolved_age == age_group) and (resolved_level == competition_level)
    return age_data[resolved_level], resolved_age, resolved_level, exact


def build_benchmark_context(sport: str, age_group: Optional[str], competition_level: Optional[str]) -> Dict[str, Any]:
    bands, resolved_age, resolved_level, exact = get_benchmark_bands(sport, age_group, competition_level)
    return {
        "resolved_age_group": resolved_age,
        "resolved_competition_level": resolved_level,
        "is_exact_match": exact,
        "metric_bands": bands,
        "classification_scale": CLASSIFICATION_LEVELS,
    }


EXERCISE_LIBRARY: List[Dict[str, Any]] = [
    {
        "id": "GEN-SPD-01", "sport": "any", "target_skill": "acceleration",
        "category": "Physical", "name": "10m Resisted Sled Sprints",
        "difficulty": "Intermediate", "equipment": ["sled", "harness", "20m marked lane"],
        "default_sets": 6, "default_reps": "10m sprint", "default_rest_s": 90,
        "safety_notes": "Keep resistance under 15% body mass to preserve sprint mechanics; full recovery between reps.",
    },
    {
        "id": "GEN-SPD-02", "sport": "any", "target_skill": "top_speed",
        "category": "Physical", "name": "Flying 20m Sprints",
        "difficulty": "Advanced", "equipment": ["30m marked lane", "timing gates (optional)"],
        "default_sets": 5, "default_reps": "20m at full speed after 10m build-up", "default_rest_s": 180,
        "safety_notes": "Requires a full dynamic warm-up; stop the session if hamstring tightness appears.",
    },
    {
        "id": "GEN-END-01", "sport": "any", "target_skill": "fatigue_resistance",
        "category": "Physical", "name": "Small-Sided Games Interval Circuit",
        "difficulty": "Intermediate", "equipment": ["cones", "bibs", "ball"],
        "default_sets": 4, "default_reps": "4min work", "default_rest_s": 120,
        "safety_notes": "Monitor RPE; stop early if technique visibly degrades from fatigue.",
    },
    {
        "id": "GEN-JMP-01", "sport": "any", "target_skill": "jump_height",
        "category": "Physical", "name": "Depth Jumps to Vertical Jump",
        "difficulty": "Advanced", "equipment": ["12-18in plyo box"],
        "default_sets": 4, "default_reps": 5, "default_rest_s": 120,
        "safety_notes": "Requires an existing strength base; not for athletes with recent lower-limb injury history.",
    },
    {
        "id": "GEN-JMP-02", "sport": "any", "target_skill": "jump_height",
        "category": "Physical", "name": "Trap Bar Jump Squats",
        "difficulty": "Intermediate", "equipment": ["trap bar", "light-moderate plates"],
        "default_sets": 4, "default_reps": 6, "default_rest_s": 120,
        "safety_notes": "Load light enough that bar speed stays fast; technique breakdown ends the set.",
    },
    {
        "id": "GEN-STB-01", "sport": "any", "target_skill": "landing_stability",
        "category": "Physical", "name": "Single-Leg Box Landings with Stick",
        "difficulty": "Beginner", "equipment": ["low box or step"],
        "default_sets": 3, "default_reps": 8, "default_rest_s": 60,
        "safety_notes": "Coach must visually confirm a controlled 'stuck' landing before progressing height.",
    },
    {
        "id": "GEN-STB-02", "sport": "any", "target_skill": "balance",
        "category": "Physical", "name": "Single-Leg RDL with Reach",
        "difficulty": "Beginner", "equipment": ["light dumbbell (optional)"],
        "default_sets": 3, "default_reps": 10, "default_rest_s": 60,
        "safety_notes": "Keep a soft knee on the standing leg; stop if sharp pain (not fatigue) appears.",
    },
    {
        "id": "GEN-REC-01", "sport": "any", "target_skill": "recovery",
        "category": "Recovery", "name": "Low-Intensity Mobility & Breathing Flow",
        "difficulty": "Beginner", "equipment": ["mat"],
        "default_sets": 1, "default_reps": "15min flow", "default_rest_s": 0,
        "safety_notes": "Never used as a substitute for a missed rest day, only as an active-recovery addition.",
    },
    {
        "id": "FB-TEC-01", "sport": "Football", "target_skill": "ball_control",
        "category": "Technical", "name": "Rondo Under Pressure (4v1/5v2)",
        "difficulty": "Intermediate", "equipment": ["ball", "cones", "bibs"],
        "default_sets": 4, "default_reps": "3min rounds", "default_rest_s": 90,
        "safety_notes": "Keep grid size appropriate to group speed to avoid collisions.",
    },
    {
        "id": "FB-TAC-01", "sport": "Football", "target_skill": "decision_making",
        "category": "Tactical", "name": "Positional Small-Sided Games with Directional Rules",
        "difficulty": "Intermediate", "equipment": ["ball", "cones", "bibs"],
        "default_sets": 3, "default_reps": "6min rounds", "default_rest_s": 120,
        "safety_notes": "Rotate roles to avoid overload on any single player's decision load.",
    },
    {
        "id": "BB-TEC-01", "sport": "Basketball", "target_skill": "ball_control",
        "category": "Technical", "name": "Two-Ball Dribble Series Under Defensive Pressure",
        "difficulty": "Intermediate", "equipment": ["2 basketballs", "cones"],
        "default_sets": 4, "default_reps": "45s", "default_rest_s": 60,
        "safety_notes": "Progress pressure only once control is maintained at game pace.",
    },
    {
        "id": "BB-TAC-01", "sport": "Basketball", "target_skill": "decision_making",
        "category": "Tactical", "name": "3v2 / 2v1 Fast Break Reads",
        "difficulty": "Intermediate", "equipment": ["ball", "half court"],
        "default_sets": 6, "default_reps": "1 rep per group", "default_rest_s": 45,
        "safety_notes": "Enforce controlled landings on finishes to protect knees/ankles.",
    },
    {
        "id": "VB-TEC-01", "sport": "Volleyball", "target_skill": "approach_timing",
        "category": "Technical", "name": "3-Step Approach Timing off a Tossed Ball",
        "difficulty": "Intermediate", "equipment": ["ball", "net"],
        "default_sets": 5, "default_reps": 6, "default_rest_s": 60,
        "safety_notes": "Watch for consistent double-leg landings to protect the patellar tendon.",
    },
    {
        "id": "VB-STB-01", "sport": "Volleyball", "target_skill": "landing_stability",
        "category": "Physical", "name": "Block-Jump Repeated Landings",
        "difficulty": "Intermediate", "equipment": ["net"],
        "default_sets": 4, "default_reps": 6, "default_rest_s": 90,
        "safety_notes": "Cap total weekly jump count to manage patellar tendon load.",
    },
    {
        "id": "HB-TEC-01", "sport": "Handball", "target_skill": "throwing_power",
        "category": "Technical", "name": "Rotational Med-Ball Throws for Shot Power",
        "difficulty": "Intermediate", "equipment": ["medicine ball", "wall"],
        "default_sets": 4, "default_reps": 6, "default_rest_s": 90,
        "safety_notes": "Warm up the shoulder and trunk thoroughly; stop on any shoulder pain.",
    },
    {
        "id": "HB-TAC-01", "sport": "Handball", "target_skill": "decision_making",
        "category": "Tactical", "name": "6v6 Transition Game With Fast-Break Bonus Rule",
        "difficulty": "Intermediate", "equipment": ["ball", "full court"],
        "default_sets": 3, "default_reps": "5min rounds", "default_rest_s": 120,
        "safety_notes": "Rotate goalkeepers; monitor collisions in the transition lane.",
    },
]


def get_relevant_exercises(sport: str, target_skills: List[str], max_items: int = 12) -> List[Dict[str, Any]]:
    """Shortlist exercises for a sport + list of weak/target skills.
    Sport-specific drills are included first, then generic ('any') drills."""
    target_skills = set(target_skills or [])
    sport_specific = [
        ex for ex in EXERCISE_LIBRARY
        if ex["sport"] == sport and (not target_skills or ex["target_skill"] in target_skills)
    ]
    generic = [
        ex for ex in EXERCISE_LIBRARY
        if ex["sport"] == "any" and (not target_skills or ex["target_skill"] in target_skills)
    ]
    combined = sport_specific + generic
    if not combined:
        # fall back to all drills for the sport (or generic) rather than an empty shortlist
        combined = [ex for ex in EXERCISE_LIBRARY if ex["sport"] in (sport, "any")]
    return combined[:max_items]



PRINCIPLES: List[str] = [
    "Progressive overload: increase volume or intensity by roughly 5-10% per week, never both sharply at once.",
    "Acute:chronic workload ratio outside ~0.8-1.3 is associated with elevated soft-tissue injury risk; flag sharp week-over-week load spikes.",
    "A fatigue_index above roughly 0.3 within a single session (large second-half drop-off in speed) suggests conditioning or pacing issues worth addressing before adding sprint volume.",
    "Landing stability and balance scores below the 'Average' band are commonly linked to higher non-contact lower-limb injury risk (ACL/ankle); prioritize neuromuscular control work before increasing plyometric intensity.",
    "Technical drills are most transferable when run under representative fatigue and decision-making pressure, not in isolation.",
    "At least one full rest day per 5-7 training days, and a lighter deload week roughly every 3-6 weeks, supports long-term adaptation without overtraining.",
    "Sleep of 8-10 hours for youth athletes and 7-9 hours for adults is consistently linked to better recovery and reduced injury incidence.",
    "Never compare metrics across different sports, ages, genders, or competition levels; only compare within the same cohort.",
]



def build_knowledge_context(
    sport: str,
    age: Optional[int],
    competition_level: Optional[str],
    weak_skill_hints: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build the full knowledge-base slice to inject into the LLM payload for
    one analysis request: relevant benchmark bands + a shortlisted exercise
    library + coaching principles + a disclaimer. Deterministic, no LLM calls."""

    age_group = _age_to_group(age)
    benchmark_context = build_benchmark_context(sport, age_group, competition_level)
    exercises = get_relevant_exercises(sport, weak_skill_hints or [], max_items=12)

    return {
        "kb_version": KB_VERSION,
        "disclaimer": KB_DISCLAIMER,
        "benchmark_reference": benchmark_context,
        "exercise_shortlist": exercises,
        "coaching_principles": PRINCIPLES,
        "instructions_for_model": (
            "Use benchmark_reference.metric_bands to classify every numeric metric into "
            "benchmark_reference.classification_scale. If benchmark_reference.is_exact_match is "
            "false, explicitly say the comparison uses the closest available age group / "
            "competition level as an approximation. Build the training plan primarily from "
            "exercise_shortlist; you may add a closely related exercise only if none in the "
            "shortlist fits, and must say why in Why Selected. Ground WHY sections and "
            "recovery/injury-prevention reasoning in coaching_principles where relevant."
        ),
    }


def _age_to_group(age: Optional[int]) -> str:
    if age is None:
        return "Senior"
    if age <= 13:
        return "U13"
    if age <= 15:
        return "U15"
    if age <= 17:
        return "U17"
    if age <= 19:
        return "U19"
    return "Senior"