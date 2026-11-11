"""
Template for a locked-down admin API. Untested against your real auth code.

Wire it up in main.py:
    from admin_router import router as admin_router
    app.include_router(admin_router)

Before using it:
  1. Add the audit_log table to SCHEMA in models.py (see the chat reply).
  2. Point the get_current_user import at YOUR auth code. It must return the
     user row loaded from the database (including id and role).
"""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import insert, select, update

from Auth_manager import get_current_user  # <-- ADJUST to match your project
from models import tables
from user_db import engine

users = tables["users"]
audit = tables["audit_log"]


def require_admin(user=Depends(get_current_user)):
    # Anything that is not exactly "admin" is a normal user (this includes NULL).
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only")
    return user


# The dependency is set once on the router, so every route added to it later
# is protected automatically and you can't forget it on a new endpoint.
router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class UserOut(BaseModel):  # no password field, so it can never be returned
    id: int
    username: str
    email: str
    role: str | None = None
    age: int | None = None
    co2eqkg: int | None = None


class RoleChange(BaseModel):
    role: Literal["user", "admin"]  # anything else is rejected with a 422


@router.get("/users", response_model=list[UserOut])
def list_users():
    cols = [users.c.id, users.c.username, users.c.email, users.c.role, users.c.age, users.c.co2eqkg]
    with engine.connect() as conn:
        rows = conn.execute(select(*cols).order_by(users.c.id)).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/users/{user_id}/role")
def change_role(user_id: int, body: RoleChange, admin=Depends(require_admin)):
    # Admins can't change their own role, so there is always at least one admin left.
    if user_id == admin["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't change your own role")

    with engine.begin() as conn:  # one transaction: the change and its audit entry succeed or fail together
        target = conn.execute(select(users.c.username).where(users.c.id == user_id)).first()
        if target is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No such user")

        conn.execute(update(users).where(users.c.id == user_id).values(role=body.role))
        conn.execute(
            insert(audit).values(
                user_id=admin["id"],
                action="change_role",
                detail=f"{target.username} -> {body.role}",
                created_at=datetime.now(timezone.utc),
            )
        )
    return {"ok": True}