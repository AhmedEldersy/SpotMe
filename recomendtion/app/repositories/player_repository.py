from sqlalchemy.orm import Session
from app.models.player import Player
from app.schemas.player import PlayerCreate


def get_all_players(db: Session):
    players = db.query(Player).all()

    return [
        {
            "id": player.id,
            "full_name": player.full_name,
            "age": player.age,
            "sport": player.sport,
            "position": player.position,
        }
        for player in players
    ]


def search_players(db: Session, name: str):
    players = (
        db.query(Player)
        .filter(Player.full_name.ilike(f"%{name}%"))
        .all()
    )

    return [
        {
            "id": player.id,
            "full_name": player.full_name,
            "age": player.age,
            "sport": player.sport,
            "position": player.position,
        }
        for player in players
    ]


def create_player(db: Session, player: PlayerCreate):
    new_player = Player(
        full_name=player.full_name,
        age=player.age,
        sport=player.sport,
        position=player.position,
        country=player.country,
        city=player.city,
        height=player.height,
        weight=player.weight,
        current_club=player.current_club,
        experience_years=player.experience_years,
        email=player.email,
        phone=player.phone
    )

    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    return new_player


def update_player(db: Session, player_id: int, player_data):
    player = db.query(Player).filter(Player.id == player_id).first()

    if not player:
        return None

    player.full_name = player_data.full_name
    player.age = player_data.age
    player.sport = player_data.sport
    player.position = player_data.position
    player.country = player_data.country
    player.city = player_data.city
    player.height = player_data.height
    player.weight = player_data.weight
    player.current_club = player_data.current_club
    player.experience_years = player_data.experience_years
    player.email = player_data.email
    player.phone = player_data.phone

    db.commit()
    db.refresh(player)

    return player


def delete_player(db: Session, player_id: int):
    player = db.query(Player).filter(Player.id == player_id).first()

    if not player:
        return None

    db.delete(player)
    db.commit()

    return {"message": "Player deleted successfully"}


from sqlalchemy import and_

def filter_players(
    db: Session,
    sport=None,
    position=None,
    min_age=None,
    max_age=None,
):
    query = db.query(Player)

    if sport:
        query = query.filter(Player.sport == sport)

    if position:
        query = query.filter(Player.position == position)

    if min_age is not None:
        query = query.filter(Player.age >= min_age)

    if max_age is not None:
        query = query.filter(Player.age <= max_age)

    players = query.all()

    return [
        {
            "id": player.id,
            "full_name": player.full_name,
            "age": player.age,
            "sport": player.sport,
            "position": player.position,
        }
        for player in players
    ]