from sqlalchemy.orm import Session
from app.models.club import Club
from app.schemas.club import ClubCreate


def get_all_clubs(db: Session):
    return db.query(Club).all()


def create_club(db: Session, club: ClubCreate):
    new_club = Club(
        name=club.name,
        country=club.country,
        city=club.city,
        sport=club.sport,
        founded=club.founded,
        stadium=club.stadium,
    )

    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    return new_club