from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import delete, insert, select, update, or_

from Auth_manager import get_curr_user
from models import tables
from user_db import engine

users = tables["users"]
audit = tables["audit_log"]
footprint = tables["footprint_log"]


def require_admin(user=Depends(get_curr_user)):
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str = "user"
    status: str = "pending"
    age: Optional[int] = None
    co2eqkg: Optional[int] = 0
    target_co2eqkg: Optional[int] = 2000
    area: Optional[str] = None
    oauth_provider: Optional[str] = "local"
    avatar_url: Optional[str] = None


class StatusUpdate(BaseModel):
    status: Literal["approved", "rejected", "pending", "suspended"]


class RoleUpdate(BaseModel):
    role: Literal["user", "admin"]


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Literal["user", "admin"]] = None
    status: Optional[Literal["approved", "rejected", "pending", "suspended"]] = None
    age: Optional[int] = None
    co2eqkg: Optional[int] = None
    target_co2eqkg: Optional[int] = None
    area: Optional[str] = None


@router.get("/users", response_model=list[UserOut])
def list_users():
    cols = [
        users.c.id,
        users.c.username,
        users.c.email,
        users.c.role,
        users.c.status,
        users.c.age,
        users.c.co2eqkg,
        users.c.target_co2eqkg,
        users.c.area,
        users.c.oauth_provider,
        users.c.avatar_url,
    ]
    with engine.connect() as conn:
        rows = conn.execute(select(*cols).order_by(users.c.id.desc())).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/users/{user_id}/status")
def change_status(user_id: int, body: StatusUpdate, admin=Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own account status"
        )

    with engine.begin() as conn:
        target = conn.execute(
            select(users.c.username, users.c.status).where(users.c.id == user_id)
        ).first()

        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        conn.execute(
            update(users).where(users.c.id == user_id).values(status=body.status)
        )

        conn.execute(
            insert(audit).values(
                user_id=admin["id"],
                action=f"status_{body.status}",
                detail=f"Admin {admin['username']} changed {target.username} status from {target.status} to {body.status}",
                created_at=datetime.now(timezone.utc),
            )
        )

    return {"ok": True, "user_id": user_id, "status": body.status}


@router.patch("/users/{user_id}/role")
def change_role(user_id: int, body: RoleUpdate, admin=Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )

    with engine.begin() as conn:
        target = conn.execute(
            select(users.c.username).where(users.c.id == user_id)
        ).first()

        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        conn.execute(
            update(users).where(users.c.id == user_id).values(role=body.role)
        )

        conn.execute(
            insert(audit).values(
                user_id=admin["id"],
                action="change_role",
                detail=f"Admin {admin['username']} set role of {target.username} to {body.role}",
                created_at=datetime.now(timezone.utc),
            )
        )

    return {"ok": True, "user_id": user_id, "role": body.role}


@router.patch("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, admin=Depends(require_admin)):
    # Prevent admin from removing their own admin status
    if user_id == admin["id"] and body.role and body.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote yourself from admin"
        )

    with engine.begin() as conn:
        target = conn.execute(
            select(users).where(users.c.id == user_id)
        ).mappings().first()

        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Collect fields to update
        values_to_update = {}
        for field, val in body.model_dump(exclude_unset=True).items():
            if val is not None:
                values_to_update[field] = val

        if not values_to_update:
            return {"ok": True, "message": "Nothing to update"}

        # Validate unique username/email if changing
        if "username" in values_to_update and values_to_update["username"] != target["username"]:
            conflict = conn.execute(
                select(users.c.id).where(users.c.username == values_to_update["username"])
            ).first()
            if conflict:
                raise HTTPException(status_code=409, detail="Username already taken")

        if "email" in values_to_update and values_to_update["email"] != target["email"]:
            conflict = conn.execute(
                select(users.c.id).where(users.c.email == values_to_update["email"])
            ).first()
            if conflict:
                raise HTTPException(status_code=409, detail="Email already registered")

        conn.execute(
            update(users).where(users.c.id == user_id).values(**values_to_update)
        )

        details = ", ".join(f"{k}={v}" for k, v in values_to_update.items())
        conn.execute(
            insert(audit).values(
                user_id=admin["id"],
                action="update_user_data",
                detail=f"Admin {admin['username']} updated user #{user_id} ({target['username']}): {details}",
                created_at=datetime.now(timezone.utc),
            )
        )

    return {"ok": True, "updated": values_to_update}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin=Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    with engine.begin() as conn:
        target = conn.execute(
            select(users.c.username).where(users.c.id == user_id)
        ).first()

        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Delete related footprint logs
        conn.execute(delete(footprint).where(footprint.c.user_id == user_id))

        # Delete user
        conn.execute(delete(users).where(users.c.id == user_id))

        conn.execute(
            insert(audit).values(
                user_id=admin["id"],
                action="delete_user",
                detail=f"Admin {admin['username']} deleted user #{user_id} ({target.username})",
                created_at=datetime.now(timezone.utc),
            )
        )

    return {"ok": True, "deleted_id": user_id}


@router.get("/audit")
def list_audit_logs(limit: int = 50):
    with engine.connect() as conn:
        rows = conn.execute(
            select(
                audit.c.id,
                audit.c.user_id,
                audit.c.action,
                audit.c.detail,
                audit.c.created_at,
                users.c.username
            )
            .select_from(audit.outerjoin(users, audit.c.user_id == users.c.id))
            .order_by(audit.c.id.desc())
            .limit(limit)
        ).mappings().all()

    return [dict(r) for r in rows]
