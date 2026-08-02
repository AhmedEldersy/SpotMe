from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.base import Base


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    country = Column(String)

    city = Column(String)

    sport = Column(String)

    founded = Column(Integer)

    stadium = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    