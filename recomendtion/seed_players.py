from app.database.session import SessionLocal
from app.models.player import Player
from faker import Faker
import random

fake = Faker()

db = SessionLocal()

sports = ["Football", "Basketball", "Handball", "Volleyball"]

football_positions = ["GK", "CB", "LB", "RB", "CM", "RW", "LW", "ST"]

clubs = [
    "Al Ahly",
    "Zamalek",
    "Pyramids",
    "Future",
    "Ismaily",
    "ENPPI",
    "Smouha",
    "Al Masry"
]

for _ in range(100):
    player = Player(
        full_name=fake.name(),
        age=random.randint(17, 35),
        sport=random.choice(sports),
        position=random.choice(football_positions),
        country="Egypt",
        city=fake.city(),
        height=random.randint(165, 200),
        weight=random.randint(60, 95),
        current_club=random.choice(clubs),
        experience_years=random.randint(0, 15),
        email=fake.email(),
        phone=fake.phone_number()
    )

    db.add(player)

db.commit()
db.close()

print("100 Players Added Successfully 🚀")