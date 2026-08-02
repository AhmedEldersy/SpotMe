import os
from sqlalchemy import create_engine

_RECOMMENDATION_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = "sqlite:///" + os.path.join(_RECOMMENDATION_DIR, "players.db")

engine = create_engine(
    DATABASE_URL,
    echo=True
)