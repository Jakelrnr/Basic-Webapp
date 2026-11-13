import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Cookie, HTTPException, Response, status
from sqlalchemy import select

from models import tables
from user_db import engine

# Ensure .env is loaded from the backend directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.environ.get("JWT_SECRET", "Yongbokontop")
COOKIE_NAME = "session"
users = tables["users"]


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def set_session_cookie(response: Response, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=8)},
        SECRET_KEY,
        algorithm="HS256",
    )
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600 * 8,
        path="/",
        secure=os.environ.get("COOKIE_SECURE", "0") == "1",
    )


def get_curr_user(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME)
) -> dict:
    err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not logged in"
    )

    if not session_token:
        raise err

    try:
        payload = jwt.decode(
            session_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise err

    with engine.connect() as conn:
        row = conn.execute(
            select(users).where(users.c.id == user_id)
        ).mappings().first()

    if row is None:
        raise err

    # Check account approval status for non-admins
    # Admins are always permitted; pending accounts get 403
    if row["role"] != "admin" and row["status"] != "approved":
        detail = "Your account is awaiting administrator approval." if row["status"] == "pending" else f"Your account is {row['status']}."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    # Return safe user dict without password
    return {
        k: v for k, v in row.items()
        if k != "password"
    }


# Alias for compatibility
get_current_user = get_curr_user
