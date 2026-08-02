from fastapi import APIRouter, Query, status, HTTPException
from app.database.session import SessionLocal
from app.repositories.player_repository import (
    get_all_players,
    create_player,
    update_player,
    delete_player,
    search_players,
    filter_players
)
from app.schemas.player import PlayerCreate

router = APIRouter()


@router.get("/players")
def get_players():
    db = SessionLocal()

    try:
        return get_all_players(db)
    finally:
        db.close()


@router.get("/players/search")
def search_player(name: str = Query(...)):
    db = SessionLocal()

    try:
        return search_players(db, name)
    finally:
        db.close()


@router.get("/players/filter")
def filter_player(
    sport: str = None,
    position: str = None,
    min_age: int = None,
    max_age: int = None,
):
    db = SessionLocal()

    try:
        return filter_players(
            db,
            sport,
            position,
            min_age,
            max_age,
        )
    finally:
        db.close()


@router.post(
    "/players",
    status_code=status.HTTP_201_CREATED
)
def add_player(player: PlayerCreate):
    db = SessionLocal()

    try:
        return create_player(db, player)
    finally:
        db.close()


@router.put("/players/{player_id}")
def edit_player(player_id: int, player: PlayerCreate):
    db = SessionLocal()

    try:
        updated = update_player(db, player_id, player)

        if updated is None:
            raise HTTPException(
                status_code=404,
                detail="Player not found"
            )

        return updated

    finally:
        db.close()


@router.delete("/players/{player_id}")
def remove_player(player_id: int):
    db = SessionLocal()

    try:
        deleted = delete_player(db, player_id)

        if deleted is None:
            raise HTTPException(
                status_code=404,
                detail="Player not found"
            )

        return deleted

    finally:
        db.close()