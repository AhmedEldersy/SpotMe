import hashlib
import json
import os
import uuid

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "players.json")

# ----------------------------------------------------------------------
# SPORT CONFIGURATION
# ----------------------------------------------------------------------

SPORT_CONFIG = {
    "football": {
        "starters": 11,
        "formations": {
            "4-3-3": ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CM", "LW", "RW", "ST"],
            "4-4-2": ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "RM", "LM", "ST", "ST"],
            "4-2-3-1": ["GK", "CB", "CB", "LB", "RB", "CDM", "CDM", "CAM", "LW", "RW", "ST"],
            "3-5-2": ["GK", "CB", "CB", "CB", "LB", "RB", "CM", "CM", "CAM", "ST", "ST"],
        },
        "default_formation": "4-3-3",
        "position_weights": {
            "GK": {"goalkeeping": 0.6, "positioning": 0.2, "reflexes": 0.2},
            "CB": {"defense": 0.5, "physical": 0.3, "passing": 0.2},
            "LB": {"pace": 0.3, "defense": 0.3, "stamina": 0.2, "passing": 0.2},
            "RB": {"pace": 0.3, "defense": 0.3, "stamina": 0.2, "passing": 0.2},
            "CDM": {"defense": 0.4, "passing": 0.3, "stamina": 0.3},
            "CM": {"passing": 0.4, "stamina": 0.3, "vision": 0.3},
            "CAM": {"passing": 0.3, "dribbling": 0.3, "shooting": 0.2, "vision": 0.2},
            "LM": {"pace": 0.3, "passing": 0.3, "stamina": 0.4},
            "RM": {"pace": 0.3, "passing": 0.3, "stamina": 0.4},
            "LW": {"pace": 0.4, "dribbling": 0.3, "shooting": 0.3},
            "RW": {"pace": 0.4, "dribbling": 0.3, "shooting": 0.3},
            "ST": {"shooting": 0.5, "pace": 0.2, "physical": 0.3},
        },
        "ratings": ["attack", "midfield", "defense", "bench_strength", "future_potential"],
    },
    "basketball": {
        "starters": 5,
        "formations": {"default": ["PG", "SG", "SF", "PF", "C"]},
        "default_formation": "default",
        "position_weights": {
            "PG": {"passing": 0.4, "pace": 0.3, "shooting": 0.3},
            "SG": {"shooting": 0.5, "pace": 0.3, "defense": 0.2},
            "SF": {"shooting": 0.3, "defense": 0.3, "physical": 0.2, "pace": 0.2},
            "PF": {"physical": 0.4, "defense": 0.3, "shooting": 0.3},
            "C": {"physical": 0.5, "defense": 0.3, "shooting": 0.2},
        },
        "ratings": ["offense", "playmaking", "defense", "bench_strength", "future_potential"],
    },
    "handball": {
        "starters": 7,
        "formations": {"default": ["GK", "LW", "RW", "CB", "LB", "RB", "Pivot"]},
        "default_formation": "default",
        "position_weights": {
            "GK": {"goalkeeping": 0.7, "reflexes": 0.3},
            "LW": {"pace": 0.4, "shooting": 0.3, "dribbling": 0.3},
            "RW": {"pace": 0.4, "shooting": 0.3, "dribbling": 0.3},
            "CB": {"passing": 0.4, "vision": 0.3, "shooting": 0.3},
            "LB": {"shooting": 0.4, "physical": 0.3, "passing": 0.3},
            "RB": {"shooting": 0.4, "physical": 0.3, "passing": 0.3},
            "Pivot": {"physical": 0.6, "shooting": 0.2, "defense": 0.2},
        },
        "ratings": ["attack", "playmaking", "defense", "bench_strength", "future_potential"],
    },
    "volleyball": {
        "starters": 6,
        "formations": {"default": ["Setter", "Outside Hitter", "Outside Hitter", "Opposite",
                                    "Middle Blocker", "Middle Blocker"]},
        "default_formation": "default",
        "position_weights": {
            "Setter": {"passing": 0.5, "vision": 0.3, "stamina": 0.2},
            "Outside Hitter": {"shooting": 0.4, "physical": 0.3, "defense": 0.3},
            "Opposite": {"shooting": 0.5, "physical": 0.3, "stamina": 0.2},
            "Middle Blocker": {"defense": 0.5, "physical": 0.4, "stamina": 0.1},
            "Libero": {"defense": 0.6, "passing": 0.4},
        },
        "ratings": ["attack", "blocking", "defense", "bench_strength", "future_potential"],
    },
}

DEFAULT_ATTR = 50

PLAY_STYLE_KEYWORDS = {
    "possession": {"passing": 10, "vision": 8, "stamina": 4},
    "tiki": {"passing": 10, "vision": 8},
    "attack": {"shooting": 8, "pace": 6, "dribbling": 6},
    "counter": {"pace": 10, "shooting": 6},
    "press": {"stamina": 8, "defense": 6, "pace": 4},
    "high-block": {"defense": 8, "physical": 4},
    "defens": {"defense": 10, "physical": 5},
    "physical": {"physical": 10},
    "fast": {"pace": 10},
    "transition": {"pace": 8, "stamina": 6},
    "space": {"pace": 6, "shooting": 4},
    "serve-and-attack": {"shooting": 8, "physical": 4},
    "block": {"defense": 8, "physical": 4},
    "playmak": {"passing": 8, "vision": 8},
    "shoot": {"shooting": 8},
    "dribbl": {"dribbling": 8},
    "goalkeep": {"goalkeeping": 10, "reflexes": 6},
}


def play_style_weights(play_style):
    text = str(play_style or "").strip().lower()
    if not text:
        return {}
    combined = {}
    for keyword, attrs in PLAY_STYLE_KEYWORDS.items():
        if keyword in text:
            for attr, w in attrs.items():
                combined[attr] = combined.get(attr, 0) + w
    return combined


# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------

def normalize_players(players):
    """Apply default fields to a raw list of player dicts (in place) and return it.

    Every player gets a stable internal ``_id`` (a uuid). This is what the
    rest of the module uses to tell players apart -- NOT their name -- so two
    players who happen to share a name (very possible in a real dataset)
    are never confused with one another or accidentally excluded from the
    lineup because of a name collision.
    """
    for p in players:
        p.setdefault("_id", uuid.uuid4().hex)
        p.setdefault("attributes", {})
        p.setdefault("age", 25)
        p.setdefault("overall", 70)
        p.setdefault("potential", p.get("overall", 70))
        p.setdefault("locked", False)
        p.setdefault("team", "Unknown")
    return players


def load_players(path=DATA_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        players = []

        for sport, sport_players in data.items():
            for p in sport_players:
                p["sport"] = sport.lower()
                players.append(p)

    else:
        players = data

    return normalize_players(players)


def players_by_sport(players, sport):
    return [p for p in players if str(p.get("sport", "")).lower() == sport.lower()]


# ----------------------------------------------------------------------
# SCORING
# ----------------------------------------------------------------------

def attribute_value(player, attr):
    return player.get("attributes", {}).get(attr, DEFAULT_ATTR)


def position_matches(player_position, slot):
    """True if the player's own listed position is (the same as) this slot.

    Comparison is case-insensitive and whitespace-trimmed so "cb", "CB ",
    and "CB" all match. A player with no listed position never matches --
    they're only ever picked for a slot as an attribute-based fallback.
    """
    if not player_position:
        return False
    return str(player_position).strip().lower() == str(slot).strip().lower()


def tactical_fit_score(player, position, sport, avg_age_target=None, play_style=None):
    weights = SPORT_CONFIG[sport]["position_weights"].get(position, {})
    if weights:
        raw = sum(attribute_value(player, a) * w for a, w in weights.items())
    else:
        raw = player.get("overall", 70)

    overall = player.get("overall", 70)
    style_weights = play_style_weights(play_style)

    if style_weights:
        total_w = sum(style_weights.values())
        style_raw = sum(attribute_value(player, a) * w for a, w in style_weights.items()) / total_w
        score = 0.5 * raw + 0.3 * overall + 0.2 * style_raw
    else:
        score = 0.65 * raw + 0.35 * overall

    if avg_age_target:
        age_gap = abs(player.get("age", 25) - avg_age_target)
        score -= age_gap * 1.5

    if player.get("locked"):
        score += 3

    return max(0, min(100, round(score, 1)))


# ----------------------------------------------------------------------
# TEAM BUILDING
# ----------------------------------------------------------------------

def _candidates_for_slot(players, slot, used_ids, sport, avg_age_target, play_style=None):
    """Rank available players for a slot, preferring their real position.

    A striker never gets picked ahead of an actual centre-back for a CB
    slot just because his attributes happen to score well on the CB
    weighting formula. We first restrict the pool to players whose own
    ``position`` field matches the slot; only if literally nobody in the
    squad plays that position do we fall back to a pure attribute-based
    best-fit search across everyone left, so a slot never goes unfilled
    when a below-standard alternative exists.

    Returns (scored_list, used_fallback) where scored_list is a list of
    (player, score) sorted best-first.
    """
    available = [p for p in players if p["_id"] not in used_ids]

    native = [p for p in available if position_matches(p.get("position"), slot)]
    pool, used_fallback = (native, False) if native else (available, True)

    scored = [(p, tactical_fit_score(p, slot, sport, avg_age_target, play_style)) for p in pool]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored, used_fallback


def _best_slot_for_locked_player(player, remaining_slots, sport, avg_age_target, play_style=None):
    """Pick the best still-open slot for a locked (must-play) player.

    Prefers a slot matching the player's own listed position; only
    considers other slot types if none of the player's natural slots are
    still open.
    """
    slot_types = list(dict.fromkeys(remaining_slots))  # unique, order-preserving
    native_slots = [s for s in slot_types if position_matches(player.get("position"), s)]
    candidate_slots = native_slots or slot_types

    best_slot, best_score, used_fallback = None, -1, not native_slots
    for slot in candidate_slots:
        s = tactical_fit_score(player, slot, sport, avg_age_target, play_style)
        if s > best_score:
            best_score, best_slot = s, slot
    return best_slot, best_score, used_fallback


def build_lineup(players, sport, formation, play_style, avg_age_target):
    config = SPORT_CONFIG[sport]
    slots = config["formations"].get(formation, config["formations"][config["default_formation"]])

    lineup = []
    used_ids = set()
    warnings = []
    remaining_slots = list(slots)

    # Locked (must-play) players get first claim on a slot that matches
    # their own position, so a "locked" striker doesn't accidentally
    # bump a real goalkeeper out of goal.
    locked_players = [p for p in players if p.get("locked") and p["_id"] not in used_ids]
    for lp in locked_players:
        if not remaining_slots:
            break
        best_slot, best_score, used_fallback = _best_slot_for_locked_player(
            lp, remaining_slots, sport, avg_age_target, play_style
        )
        if best_slot is None:
            continue
        lineup.append(build_player_entry(lp, best_slot, best_score, sport, used_fallback))
        used_ids.add(lp["_id"])
        remaining_slots.remove(best_slot)
        if used_fallback:
            warnings.append(
                "{} is locked into {} out of position (listed as {}).".format(
                    lp.get("name", "Unknown"), best_slot, lp.get("position") or "unknown"
                )
            )

    # Fill every remaining slot, preferring a player who actually plays
    # that position over the best attribute-score match.
    missing_positions = []
    for slot in list(remaining_slots):
        scored, used_fallback = _candidates_for_slot(players, slot, used_ids, sport, avg_age_target, play_style)
        if not scored:
            message = "No player available for the {} position in our current squad.".format(slot)
            warnings.append(message)
            missing_positions.append({"position": slot, "message": message})
            continue
        best_player, best_score = scored[0]
        lineup.append(build_player_entry(best_player, slot, best_score, sport, used_fallback))
        used_ids.add(best_player["_id"])
        remaining_slots.remove(slot)
        if used_fallback:
            warnings.append(
                "No natural {} in the squad -- filled with {} (listed as {}) instead.".format(
                    slot, best_player.get("name", "Unknown"), best_player.get("position") or "unknown"
                )
            )

    return lineup, used_ids, warnings, missing_positions


def build_player_entry(player, position, score, sport, out_of_position=False):
    return {
        "position": position,
        "listed_position": player.get("position"),
        "out_of_position": out_of_position,
        "name": player.get("name", "Unknown"),
        "age": player.get("age", 25),
        "team": player.get("team", "Unknown"),
        "key_attributes": player.get("attributes", {}),
        "tactical_fit_score": score,
    }


def build_bench(players, used_ids, sport, avg_age_target, play_style=None):
    remaining = [p for p in players if p["_id"] not in used_ids]

    def _bench_rank(p):
        pos = p.get("position")
        if pos and pos in SPORT_CONFIG[sport]["position_weights"]:
            return tactical_fit_score(p, pos, sport, avg_age_target, play_style)
        return p.get("overall", 70)

    remaining.sort(key=_bench_rank, reverse=True)

    bench = []
    for p in remaining[:8]:
        age = p.get("age", 25)
        overall = p.get("overall", 70)
        potential = p.get("potential", overall)

        if potential - overall >= 10 and age <= 21:
            role = "Future Talent"
        elif overall >= 80 and age <= 30:
            role = "Game Changer"
        elif p.get("locked"):
            role = "Backup"
        else:
            role = "Tactical" if len(bench) % 2 == 0 else "Backup"

        bench.append({
            "position": p.get("position", "Utility"),
            "name": p.get("name", "Unknown"),
            "age": age,
            "team": p.get("team", "Unknown"),
            "role": role,
            "key_attributes": p.get("attributes", {}),
        })
    return bench


def build_chemistry(lineup, avg_age_target):
    if not lineup:
        return {"score": 0, "explanation": "No players available to evaluate."}

    fit_scores = [p["tactical_fit_score"] for p in lineup]
    avg_fit = sum(fit_scores) / len(fit_scores)
    ages = [p["age"] for p in lineup]
    age_spread = (max(ages) - min(ages)) if ages else 0

    score = avg_fit - (age_spread * 0.5)
    score = max(0, min(100, round(score)))

    explanation = (
        "Average tactical fit across the lineup is {:.1f}/100, with an age spread of {} years. "
        "Role balance is coherent across the formation, and style synergy benefits from players "
        "sharing complementary attribute profiles rather than overlapping skillsets."
    ).format(avg_fit, age_spread)

    return {"score": score, "explanation": explanation}


def build_player_analysis(lineup, sport):
    analysis = []
    for p in lineup:
        weights = SPORT_CONFIG[sport]["position_weights"].get(p["position"], {})
        top_attrs = sorted(weights.keys(), key=lambda a: weights[a], reverse=True)[:2]
        strengths = ", ".join(top_attrs) if top_attrs else "overall ability"

        if p.get("out_of_position"):
            why = (
                "Best available tactical fit ({}) for the {} role, moved from their listed "
                "position ({}) because no natural fit remained.".format(
                    p["tactical_fit_score"], p["position"], p.get("listed_position") or "unknown"
                )
            )
        else:
            why = "Highest available tactical fit ({}) for the {} role given age and " \
                  "attribute profile.".format(p["tactical_fit_score"], p["position"])

        analysis.append({
            "name": p["name"],
            "why_selected": why,
            "tactical_role": "Primary {} in the system.".format(p["position"]),
            "strengths": strengths,
            "fit_with_teammates": "Attribute profile complements neighboring roles in the "
                                   "formation without duplicating responsibilities.",
        })
    return analysis


def build_rejected_players(players, used_ids, sport, avg_age_target, limit=5):
    remaining = [p for p in players if p["_id"] not in used_ids]
    remaining.sort(key=lambda p: p.get("overall", 70), reverse=True)

    reasons_cycle = [
        "Not fitting playstyle",
        "Weak chemistry",
        "Physical mismatch",
        "Age issue",
        "Tactical limitation",
    ]

    rejected = []
    for i, p in enumerate(remaining[:limit]):
        reason = reasons_cycle[i % len(reasons_cycle)]
        if avg_age_target and abs(p.get("age", 25) - avg_age_target) > 6:
            reason = "Age issue"
        rejected.append({
            "name": p.get("name", "Unknown"),
            "reason_for_rejection": reason,
        })
    return rejected


def build_future_plan(players, used_ids, sport):
    remaining = [p for p in players if p["_id"] not in used_ids]
    young_talents = [p for p in remaining if p.get("age", 25) <= 21]
    young_talents.sort(key=lambda p: p.get("potential", p.get("overall", 70)), reverse=True)

    plan = []
    for p in young_talents[:3]:
        plan.append({
            "type": "Future Replacement",
            "name": p.get("name", "Unknown"),
            "age": p.get("age", 25),
            "note": "High potential ({}) relative to current overall ({}); development "
                    "candidate over the next 1-2 seasons.".format(
                        p.get("potential", p.get("overall", 70)), p.get("overall", 70)),
        })

    plan.append({
        "type": "Key Upgrade",
        "note": "Monitor market for a proven starter above the current squad's average overall "
                 "in the most tactically demanding position.",
    })
    plan.append({
        "type": "Long-Term Improvement",
        "note": "Gradually lower squad average age by rotating in academy/future talents "
                 "identified above without disrupting core tactical cohesion.",
    })
    return plan


def build_injury_simulation(lineup, bench, sport):
    if not lineup:
        return {}
    key_player = max(lineup, key=lambda p: p["tactical_fit_score"])
    same_position_bench = [b for b in bench if b["position"] == key_player["position"]]
    replacement = same_position_bench[0] if same_position_bench else (bench[0] if bench else None)

    return {
        "injured_player": key_player["name"],
        "position": key_player["position"],
        "replacement": replacement["name"] if replacement else "No direct replacement available",
        "impact_on_team": "Loss of a top tactical-fit player ({}) reduces overall cohesion; "
                           "team must adapt short-term.".format(key_player["tactical_fit_score"]),
        "tactical_adjustment": "Shift responsibilities to nearby roles and rely on the "
                                "replacement's closest attribute match while reinforcing "
                                "team shape around the gap.",
    }


def _stable_jitter(key):
    """A small, deterministic +/-3 offset derived from ``key``.

    The original code used Python's built-in ``hash()`` on a string, which
    is randomized per-process (PYTHONHASHSEED) unless explicitly disabled.
    That made team ratings silently shift every time the server restarted,
    even for the exact same squad and request. Using a fixed-digest hash
    (md5) makes the jitter reproducible across runs and processes.
    """
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return (int(digest, 16) % 7) - 3


def build_team_ratings(lineup, bench, sport):
    config = SPORT_CONFIG[sport]
    rating_keys = config["ratings"]

    avg_fit = (sum(p["tactical_fit_score"] for p in lineup) / len(lineup)) if lineup else 0
    bench_strength = min(100, round(avg_fit * 0.6 + len(bench) * 3))
    future_potential = min(100, round(avg_fit * 0.5 + 20))

    ratings = {}
    for key in rating_keys:
        if key == "bench_strength":
            ratings[key] = bench_strength
        elif key == "future_potential":
            ratings[key] = future_potential
        else:
            jitter = _stable_jitter(key + sport)
            ratings[key] = max(0, min(100, round(avg_fit + jitter)))
    return ratings


# ----------------------------------------------------------------------
# MAIN BUILD PER SPORT
# ----------------------------------------------------------------------

def build_team_for_sport(all_players, sport, formation=None, play_style=None, avg_age_target=None):
    config = SPORT_CONFIG[sport]
    formation = formation or config["default_formation"]
    sport_players = players_by_sport(all_players, sport)

    if not sport_players:
        return {
            "sport": sport,
            "error": "No players found for sport '{}' in dataset.".format(sport),
        }

    lineup, used_ids, warnings, missing_positions = build_lineup(
        sport_players, sport, formation, play_style, avg_age_target
    )
    bench = build_bench(sport_players, used_ids, sport, avg_age_target, play_style)
    chemistry = build_chemistry(lineup, avg_age_target)
    player_analysis = build_player_analysis(lineup, sport)
    rejected_players = build_rejected_players(sport_players, used_ids, sport, avg_age_target)
    future_plan = build_future_plan(sport_players, used_ids, sport)
    injury_simulation = build_injury_simulation(lineup, bench, sport)
    team_ratings = build_team_ratings(lineup, bench, sport)

    slots_needed = len(config["formations"].get(formation, config["formations"][config["default_formation"]]))

    return {
        "sport": sport,
        "formation": formation,
        "play_style": play_style,
        "starting_lineup": lineup,
        "is_complete": len(lineup) == slots_needed,
        "warnings": warnings,
        "missing_positions": missing_positions,
        "bench": bench,
        "chemistry": chemistry,
        "player_analysis": player_analysis,
        "rejected_players": rejected_players,
        "future_plan": future_plan,
        "injury_simulation": injury_simulation,
        "team_ratings": team_ratings,
    }


def main():
    all_players = load_players(DATA_PATH)

    requests = [
        {"sport": "football", "formation": "4-3-3", "play_style": "possession-based attacking football", "avg_age_target": 26},
        {"sport": "basketball", "formation": "default", "play_style": "pace and space", "avg_age_target": 27},
        {"sport": "handball", "formation": "default", "play_style": "fast transition handball", "avg_age_target": 25},
        {"sport": "volleyball", "formation": "default", "play_style": "high-block, serve-and-attack", "avg_age_target": 24},
    ]

    teams = []
    for req in requests:
        teams.append(build_team_for_sport(
            all_players,
            req["sport"],
            formation=req["formation"],
            play_style=req["play_style"],
            avg_age_target=req["avg_age_target"],
        ))

    print(json.dumps(teams, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()