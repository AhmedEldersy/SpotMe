from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.base import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)

    age = Column(Integer)

    sport = Column(String, nullable=False)

    position = Column(String)

    country = Column(String)

    city = Column(String)

    height = Column(Integer)

    weight = Column(Integer)

    current_club = Column(String)

    experience_years = Column(Integer)

    email = Column(String)

    phone = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)