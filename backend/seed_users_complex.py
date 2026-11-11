"""
Creates 5 test accounts: 1 admin + 4 normal users.
DEV ONLY. Never run this against a real database: the passwords below are public.

    python seed_users.py           # add any test accounts that are missing
    python seed_users.py --reset   # delete the test accounts, then add them again

Needs:  pip install bcrypt
"""
import sys

import bcrypt
from sqlalchemy import delete, insert, select

from models import sync_schema, tables
from user_db import engine

users = tables["users"]


# IMPORTANT: this must hash the same way your login code checks passwords.
# If Auth_manager.py already has a hash function, import and use that instead.
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def password_matches(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


TEST_USERS = [
    dict(username="admin_test", email="admin_test@example.com", password="AdminTest-2026!", age=35, co2eqkg=0,    role="admin"),
    dict(username="alice_test", email="alice_test@example.com", password="AliceTest-2026!", age=28, co2eqkg=1200, role="user"),
    dict(username="bob_test",   email="bob_test@example.com",   password="BobTest-2026!",   age=41, co2eqkg=3400, role="user"),
    dict(username="cara_test",  email="cara_test@example.com",  password="CaraTest-2026!",  age=19, co2eqkg=800,  role="user"),
    dict(username="dev_test",   email="dev_test@example.com",   password="DevTest-2026!",   age=52, co2eqkg=2100, role="user"),
]


def main() -> None:
    sync_schema(engine)  # makes sure the table and the role column exist
    names = [u["username"] for u in TEST_USERS]

    with engine.begin() as conn:
        if "--reset" in sys.argv:
            conn.execute(delete(users).where(users.c.username.in_(names)))
            print("removed existing test accounts")

        existing = {
            row.username
            for row in conn.execute(select(users.c.username).where(users.c.username.in_(names)))
        }
        for u in TEST_USERS:
            if u["username"] in existing:
                print(f"skip     {u['username']} (already exists)")
                continue
            values = {**u, "password": hash_password(u["password"])}
            conn.execute(insert(users).values(**values))
            print(f"created  {u['username']}  ({u['role']})")

    # Read everything back and check it, so a silent problem shows up here.
    with engine.connect() as conn:
        rows = conn.execute(select(users).where(users.c.username.in_(names))).mappings().all()

    plain = {u["username"]: u["password"] for u in TEST_USERS}
    problems = 0
    print("\nusername      role   password check")
    for r in sorted(rows, key=lambda r: r["id"]):
        ok = password_matches(plain[r["username"]], r["password"])
        problems += 0 if ok else 1
        print(f"{r['username']:<13} {str(r['role']):<6} {'OK' if ok else 'FAILED'}")

    if len(rows) != len(TEST_USERS):
        problems += 1
        print(f"\nexpected {len(TEST_USERS)} accounts, found {len(rows)}")
    print("\nall good" if problems == 0 else f"\n{problems} problem(s), see above")
    import random
    from datetime import datetime, timedelta

    log = tables["footprint_log"]
    with engine.begin() as conn:
        for r in conn.execute(select(users.c.id, users.c.co2eqkg)).all():
            for m in range(6):
                conn.execute(insert(log).values(
                    user_id=r.id,
                    co2eqkg=int((r.co2eqkg or 1000) * random.uniform(0.8, 1.2)),
                    logged_at=datetime.now() - timedelta(days=31 * (5 - m)),
                ))

if __name__ == "__main__":
    main()