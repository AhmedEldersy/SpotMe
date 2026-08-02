from fastapi import APIRouter
from app.database.session import SessionLocal
from app.repositories.club_repository import (
    get_all_clubs,
    create_club
)
from app.schemas.club import ClubCreate

router = APIRouter()


@router.get("/clubs")
def get_clubs():
    db = SessionLocal()

    try:
        return get_all_clubs(db)
    finally:
        db.close()


@router.post("/clubs")
def add_club(club: ClubCreate):
    db = SessionLocal()

    try:
        return create_club(db, club)
    finally:
        db.close()