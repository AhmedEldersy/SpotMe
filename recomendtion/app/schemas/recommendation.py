from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    sport: str
    position: str
    age: int


class RecommendationResponse(BaseModel):
    id: int
    full_name: str
    sport: str
    position: str
    score: float