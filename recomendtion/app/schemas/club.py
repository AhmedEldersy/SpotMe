from pydantic import BaseModel


class ClubCreate(BaseModel):
    name: str
    country: str
    city: str
    sport: str
    founded: int
    stadium: str