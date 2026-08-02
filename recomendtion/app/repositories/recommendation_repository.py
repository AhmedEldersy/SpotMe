from sqlalchemy.orm import Session
from app.models.player import Player





def recommend_players(db: Session, sport: str, position: str, age: int):
    players = db.query(Player).all()

    recommendations = []

    for player in players:
        score = 0

        # Sport (40)
        if player.sport.lower() == sport.lower():
            score += 40

        # Position (25)
        if player.position.lower() == position.lower():
            score += 25

        # Age (15)
        age_difference = abs(player.age - age)

        if age_difference <= 2:
            score += 15
        elif age_difference <= 5:
            score += 8

        # Experience (10)
        if player.experience_years is not None:
            if player.experience_years >= 5:
                score += 10
            elif player.experience_years >= 2:
                score += 5

        # Height (5)
        if player.height is not None:
            if 170 <= player.height <= 195:
                score += 5

        # Weight (5)
        if player.weight is not None:
            if 60 <= player.weight <= 90:
                score += 5

        if score > 0:
            recommendations.append({
                "id": player.id,
                "full_name": player.full_name,
                "sport": player.sport,
                "position": player.position,
                "score": score
            })

    recommendations.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return recommendations[:10]