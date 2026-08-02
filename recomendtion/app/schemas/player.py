from pydantic import BaseModel, EmailStr, Field


class PlayerCreate(BaseModel):
    full_name: str = Field(..., min_length=3)

    age: int = Field(..., gt=0)

    sport: str

    position: str

    country: str

    city: str

    height: float = Field(..., gt=0)

    weight: float = Field(..., gt=0)

    current_club: str

    experience_years: int = Field(..., ge=0)

    email: EmailStr

    phone: str = Field(..., min_length=8)