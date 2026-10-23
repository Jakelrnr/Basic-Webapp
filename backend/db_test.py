from sqlalchemy import select, insert
from user_db import engine
from models import tables
from Auth_manager import hash_password, verify_password

users = tables["users"]    # the Table object built from your dict

with engine.begin() as conn:        # begin() = write, saves automatically
    conn.execute(insert(users).values(
        username="alice", email="a@x.com",
        password=hash_password("secret123"),
    ))

with engine.connect() as conn:      # connect() = read
    row = conn.execute(select(users)).mappings().first()
    print(dict(row))
    print(verify_password("secret123", row["password"]))   # True
    print(verify_password("wrong", row["password"]))       # False