from fastapi import APIRouter
from app.database.session import SessionLocal
from app.repositories.recommendation_repository import recommend_players
from app.schemas.recommendation import RecommendationRequest

router = APIRouter()


@router.post("/recommend-player")
def recommend(request: RecommendationRequest):
    db = SessionLocal()

    try:
        result = recommend_players(
            db=db,
            sport=request.sport,
            position=request.position,
            age=request.age
        )

        return result

    finally:
        db.close()