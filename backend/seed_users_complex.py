
"""
Create 5 development test accounts: 1 admin + 4 normal users.

DEV ONLY — never run against a production database.
The test passwords in this file are public.

Usage:
    python seed_users.py
        Add missing test accounts and missing footprint history.

    python seed_users.py --reset
        Delete the test accounts and their footprint history, then recreate them.

Requires:
    pip install bcrypt
"""

import sys
import random
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import delete, insert, select

from models import sync_schema, tables
from user_db import engine


users = tables["users"]
footprint_log = tables["footprint_log"]


def hash_password(plain: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def password_matches(plain: str, hashed: str) -> bool:
    """Check a plaintext password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8")
    )


TEST_USERS = [
    {
        "username": "admin_test",
        "email": "admin_test@example.com",
        "password": "AdminTest-2026!",
        "age": 35,
        "co2eqkg": 0,
        "role": "admin",
        "status": "approved",
        "oauth_provider": "local",
    },
    {
        "username": "alice_test",
        "email": "alice_test@example.com",
        "password": "AliceTest-2026!",
        "age": 28,
        "co2eqkg": 1200,
        "role": "user",
        "status": "approved",
        "oauth_provider": "local",
    },
    {
        "username": "bob_test",
        "email": "bob_test@example.com",
        "password": "BobTest-2026!",
        "age": 41,
        "co2eqkg": 3400,
        "role": "user",
        "status": "approved",
        "oauth_provider": "local",
    },
    {
        "username": "cara_test",
        "email": "cara_test@example.com",
        "password": "CaraTest-2026!",
        "age": 19,
        "co2eqkg": 800,
        "role": "user",
        "status": "pending",
        "oauth_provider": "local",
    },
    {
        "username": "dev_test",
        "email": "dev_test@example.com",
        "password": "DevTest-2026!",
        "age": 52,
        "co2eqkg": 2100,
        "role": "user",
        "status": "approved",
        "oauth_provider": "local",
    },
]


def seed_footprint_history(conn, user_id: int, co2eqkg: int) -> None:
    """Add six monthly records if this account has no history yet."""

    existing = conn.execute(
        select(footprint_log.c.id)
        .where(footprint_log.c.user_id == user_id)
        .limit(1)
    ).first()

    if existing:
        print(f"footprints skipped for user ID {user_id}")
        return

    for month in range(6):
        amount = int(
            (co2eqkg or 1000) * random.uniform(0.8, 1.2)
        )

        conn.execute(
            insert(footprint_log).values(
                user_id=user_id,
                co2eqkg=amount,
                logged_at=datetime.now() - timedelta(
                    days=31 * (5 - month)
                ),
            )
        )

    print(f"footprints created for user ID {user_id}")


def main() -> None:
    # Ensure the database tables and columns exist.
    sync_schema(engine)

    names = [user["username"] for user in TEST_USERS]
    reset = "--reset" in sys.argv

    with engine.begin() as conn:

        # Remove existing test data when resetting.
        if reset:
            test_ids = select(users.c.id).where(
                users.c.username.in_(names)
            )

            conn.execute(
                delete(footprint_log).where(
                    footprint_log.c.user_id.in_(test_ids)
                )
            )

            conn.execute(
                delete(users).where(
                    users.c.username.in_(names)
                )
            )

            print("Existing test accounts and footprint history removed.")

        # Find accounts that already exist.
        existing = {
            row.username
            for row in conn.execute(
                select(users.c.username).where(
                    users.c.username.in_(names)
                )
            )
        }

        # Create missing accounts.
        for user in TEST_USERS:
            username = user["username"]

            if username in existing:
                print(f"SKIPPED  {username} (already exists)")
                continue

            values = {
                **user,
                "password": hash_password(user["password"]),
            }

            conn.execute(
                insert(users).values(**values)
            )

            print(
                f"CREATED  {username} "
                f"({user['role']}, {user['status']})"
            )

        # Add missing footprint history for test accounts only.
        test_rows = conn.execute(
            select(users.c.id, users.c.username, users.c.co2eqkg)
            .where(users.c.username.in_(names))
        ).all()

        for row in test_rows:
            seed_footprint_history(
                conn,
                row.id,
                row.co2eqkg or 1000
            )

    # Read accounts back and verify their passwords and account types.
    with engine.connect() as conn:
        rows = conn.execute(
            select(users).where(users.c.username.in_(names))
        ).mappings().all()

    expected = {
        user["username"]: user
        for user in TEST_USERS
    }

    problems = 0

    print("\nACCOUNT CHECK")
    print("-" * 65)
    print(
        f"{'USERNAME':<14} "
        f"{'ROLE':<8} "
        f"{'STATUS':<10} "
        f"PASSWORD"
    )
    print("-" * 65)

    for row in sorted(rows, key=lambda item: item["id"]):
        test_user = expected[row["username"]]

        password_ok = password_matches(
            test_user["password"],
            row["password"]
        )

        role_ok = row["role"] == test_user["role"]
        status_ok = row["status"] == test_user["status"]

        all_ok = password_ok and role_ok and status_ok

        if not all_ok:
            problems += 1

        print(
            f"{row['username']:<14} "
            f"{str(row['role']):<8} "
            f"{str(row['status']):<10} "
            f"{'OK' if all_ok else 'FAILED'}"
        )

    if len(rows) != len(TEST_USERS):
        problems += 1
        print(
            f"\nExpected {len(TEST_USERS)} accounts, "
            f"but found {len(rows)}."
        )

    print("-" * 65)

    if problems == 0:
        print("All test accounts passed verification.")
    else:
        print(f"{problems} problem(s) found. Check the output above.")


if __name__ == "__main__":
    main()
