#!/usr/bin/python3

from sqlalchemy.orm.session import Session
from sqlalchemy.sql.functions import func
from api.dependencies.db import get_db
from api.core.security import get_password_hash
from api.models import User, Prospect, Campaign, CampaignProspect, File

from random import randint
from datetime import timedelta


def seed_data(db: Session):
    print("-- Seeding Data --")
    # Create user
    user1 = User(email="test@test.com", password_digest=get_password_hash("sample"))
    db.add(user1)

    for i in range(20):
        # Create campaigns for user
        campaign = Campaign(name=f"Campaign {i}", user=user1)
        db.add(campaign)
        for j in range(0, 10):
            # Create prospects for user
            prospect = Prospect(
                email=f"prospect{i}{j}@mail.com",
                user=user1,
                first_name=f"John {i}{j}",
                last_name="D.",
            )
            db.add(prospect)
            # Link the prospects to a campaign
            link = CampaignProspect(prospect=prospect, campaign=campaign)
            db.add(link)

    for i in range(10):
        num_rows = randint(10, 100000)
        file_size = num_rows * randint(8, 1024)
        done_at = func.now() + timedelta(milliseconds=(num_rows * randint(1, 10)))
        file = File(
            filename=f"file{i}",
            total_rows=num_rows,
            done_rows=num_rows,
            file_size=file_size,
            done_at=done_at,
            user=user1,
        )
        db.add(file)

    try:
        db.commit()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    db = next(get_db())
    seed_data(db)
