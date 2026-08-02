from app.database.connection import engine
from app.database.base import Base

from app.models.player import Player

Base.metadata.create_all(bind=engine)

print("✅ Database Created Successfully")