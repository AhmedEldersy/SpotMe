from typing import Any, Dict, List, Optional
from threading import Lock
import json
import os

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import team_builder as tb

router = APIRouter()

PLAYERS: List[Dict[str, Any]] = []
PLAYERS_LOCK = Lock()


class Player(BaseModel):
    name: str = Field(..., min_length=1)
    sport: str = Field(..., min_length=1)
    position: Optional[str] = None
    team: Optional[str] = "Unknown"
    age: Optional[int] = Field(25, ge=14, le=50)
    overall: Optional[int] = Field(70, ge=0, le=100)
    potential: Optional[int] = Field(None, ge=0, le=100)
    locked: Optional[bool] = False
    attributes: Optional[Dict[str, float]] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    sport: Optional[str] = None
    position: Optional[str] = None
    team: Optional[str] = None
    age: Optional[int] = Field(None, ge=14, le=50)
    overall: Optional[int] = Field(None, ge=0, le=100)
    potential: Optional[int] = Field(None, ge=0, le=100)
    locked: Optional[bool] = None
    attributes: Optional[Dict[str, float]] = None

    class Config:
        extra = "allow"


class BuildTeamRequest(BaseModel):
    sport: str = Field(..., description="One of: football, basketball, handball, volleyball")
    formation: Optional[str] = Field(None, description="Formation key; defaults to the sport's default formation")
    play_style: Optional[str] = Field(None, description="Free-text label describing the desired play style")
    avg_age_target: Optional[float] = Field(None, gt=0, le=60, description="Target average squad age used to bias player fit scores")


class BuildAllRequest(BaseModel):
    requests: List[BuildTeamRequest] = Field(..., min_items=1)


def _validate_sport(sport: str) -> str:
    sport = sport.lower().strip()
    if sport not in tb.SPORT_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown sport '{}'. Valid sports: {}".format(
                sport, ", ".join(tb.SPORT_CONFIG.keys())
            ),
        )
    return sport


def _validate_formation(sport: str, formation: Optional[str]) -> None:
    if formation is None:
        return
    valid = tb.SPORT_CONFIG[sport]["formations"]
    if formation not in valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown formation '{}' for sport '{}'. Valid formations: {}".format(
                formation, sport, ", ".join(valid.keys())
            ),
        )


def _player_key(p: Dict[str, Any]):
    return (str(p.get("name", "")).strip().lower(), str(p.get("sport", "")).strip().lower())


def _find_player_index(player_id: str) -> int:
    for i, p in enumerate(PLAYERS):
        if p.get("_id") == player_id:
            return i
    return -1


async def unhandled_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error: {}".format(str(exc))},
    )


@router.get("/health", tags=["system"])
def health():
    return {"status": "ok", "players_loaded": len(PLAYERS)}


@router.get("/sports", tags=["system"])
def list_sports():
    return {
        sport: {
            "starters": cfg["starters"],
            "formations": {name: slots for name, slots in cfg["formations"].items()},
            "default_formation": cfg["default_formation"],
            "ratings": cfg["ratings"],
        }
        for sport, cfg in tb.SPORT_CONFIG.items()
    }


@router.get("/stats", tags=["system"])
def stats():
    by_sport: Dict[str, Dict[str, Any]] = {}
    for p in PLAYERS:
        sport = str(p.get("sport", "unknown")).lower()
        bucket = by_sport.setdefault(sport, {"count": 0, "avg_overall": 0.0, "avg_age": 0.0})
        bucket["count"] += 1
        bucket["avg_overall"] += p.get("overall", 70)
        bucket["avg_age"] += p.get("age", 25)

    for sport, bucket in by_sport.items():
        if bucket["count"]:
            bucket["avg_overall"] = round(bucket["avg_overall"] / bucket["count"], 1)
            bucket["avg_age"] = round(bucket["avg_age"] / bucket["count"], 1)

    return {"total_players": len(PLAYERS), "by_sport": by_sport}


@router.post("/players", status_code=status.HTTP_201_CREATED, tags=["players"])
def upload_players(
    players: List[Player],
    mode: str = Query(
        "replace",
        description="'replace' swaps out the entire dataset with this payload. "
                    "'merge' keeps everything already loaded and only adds/updates "
                    "players from this payload (matched by name+sport) -- use this "
                    "when adding one sport's roster without losing the others.",
    ),
):
    global PLAYERS

    if mode not in ("replace", "merge"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mode must be 'replace' or 'merge', got '{}'.".format(mode),
        )

    if not players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must contain at least one player.",
        )

    raw = []
    for p in players:
        d = {k: v for k, v in p.dict().items() if v is not None}
        d["sport"] = str(d.get("sport", "")).strip().lower()
        if not d["sport"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Every player must have a non-empty 'sport'.",
            )
        raw.append(d)

    incoming = tb.normalize_players(raw)

    with PLAYERS_LOCK:
        if mode == "replace":
            PLAYERS = incoming
        else:
            existing_index = {_player_key(p): i for i, p in enumerate(PLAYERS)}
            for p in incoming:
                key = _player_key(p)
                if key in existing_index:
                    PLAYERS[existing_index[key]] = p
                else:
                    PLAYERS.append(p)
                    existing_index[key] = len(PLAYERS) - 1

    return {"players_loaded": len(PLAYERS), "mode": mode}


@router.get("/players", tags=["players"])
def get_players(
    sport: Optional[str] = None,
    team: Optional[str] = None,
    position: Optional[str] = None,
    name: Optional[str] = None,
    locked: Optional[bool] = None,
    min_overall: Optional[int] = Query(None, ge=0, le=100),
    max_age: Optional[int] = Query(None, ge=0),
    sort_by: Optional[str] = Query(None, description="overall, age, potential, or name"),
    descending: bool = True,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    result = PLAYERS

    if sport:
        sport = _validate_sport(sport)
        result = [p for p in result if str(p.get("sport", "")).lower() == sport]
    if team:
        result = [p for p in result if str(p.get("team", "")).lower() == team.lower()]
    if position:
        result = [p for p in result if str(p.get("position", "")).lower() == position.lower()]
    if name:
        result = [p for p in result if name.lower() in str(p.get("name", "")).lower()]
    if locked is not None:
        result = [p for p in result if bool(p.get("locked", False)) == locked]
    if min_overall is not None:
        result = [p for p in result if p.get("overall", 70) >= min_overall]
    if max_age is not None:
        result = [p for p in result if p.get("age", 25) <= max_age]

    valid_sort_keys = {"overall", "age", "potential", "name"}
    if sort_by:
        if sort_by not in valid_sort_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sort_by must be one of: {}".format(", ".join(valid_sort_keys)),
            )
        result = sorted(result, key=lambda p: p.get(sort_by, 0) or 0, reverse=descending)

    total = len(result)
    page = result[offset: offset + limit]

    return {"total": total, "limit": limit, "offset": offset, "players": page}


@router.get("/players/{player_id}", tags=["players"])
def get_player(player_id: str):
    idx = _find_player_index(player_id)
    if idx == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found.")
    return PLAYERS[idx]


@router.patch("/players/{player_id}", tags=["players"])
def update_player(player_id: str, patch: PlayerUpdate):
    with PLAYERS_LOCK:
        idx = _find_player_index(player_id)
        if idx == -1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found.")

        updates = {k: v for k, v in patch.dict(exclude_unset=True).items() if v is not None}
        if "sport" in updates:
            updates["sport"] = str(updates["sport"]).strip().lower()

        PLAYERS[idx].update(updates)
        return PLAYERS[idx]


@router.delete("/players/{player_id}", tags=["players"])
def delete_player(player_id: str):
    with PLAYERS_LOCK:
        idx = _find_player_index(player_id)
        if idx == -1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found.")
        removed = PLAYERS.pop(idx)
    return {"deleted": removed.get("name", "Unknown"), "players_loaded": len(PLAYERS)}


@router.delete("/players", tags=["players"])
def clear_players():
    global PLAYERS
    with PLAYERS_LOCK:
        PLAYERS = []
    return {"players_loaded": 0}


@router.post("/players/load-from-disk", tags=["players"])
def load_players_from_disk():
    global PLAYERS
    try:
        loaded = tb.load_players(tb.DATA_PATH)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to load players: {}".format(e))

    with PLAYERS_LOCK:
        PLAYERS = loaded
    return {"players_loaded": len(PLAYERS)}


@router.post("/players/save-to-disk", tags=["players"])
def save_players_to_disk():
    directory = os.path.dirname(tb.DATA_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(tb.DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(PLAYERS, f, ensure_ascii=False, indent=2)

    return {"players_saved": len(PLAYERS), "path": tb.DATA_PATH}


@router.post("/team/build", tags=["team"])
def build_team(req: BuildTeamRequest):
    if not PLAYERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No players loaded. POST /players (or /players/load-from-disk) first.",
        )
    sport = _validate_sport(req.sport)
    _validate_formation(sport, req.formation)

    result = tb.build_team_for_sport(
        PLAYERS,
        sport,
        formation=req.formation,
        play_style=req.play_style,
        avg_age_target=req.avg_age_target,
    )
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.post("/team/build-all", tags=["team"])
def build_all_teams(body: BuildAllRequest):
    if not PLAYERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No players loaded. POST /players (or /players/load-from-disk) first.",
        )
    results = []
    for req in body.requests:
        sport = _validate_sport(req.sport)
        _validate_formation(sport, req.formation)
        results.append(
            tb.build_team_for_sport(
                PLAYERS,
                sport,
                formation=req.formation,
                play_style=req.play_style,
                avg_age_target=req.avg_age_target,
            )
        )
    return {"teams": results}