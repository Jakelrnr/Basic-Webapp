import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, insert, update, delete, or_, func

from models import tables, sync_schema
from user_db import engine
from Auth_manager import (
    COOKIE_NAME,
    get_curr_user,
    set_session_cookie,
    verify_password,
    hash_password,
)
from admin_route import router as admin_router

# Load environment
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

users = tables["users"]
log = tables["footprint_log"]
audit = tables["audit_log"]

app = FastAPI(title="Carbon Footprint & KPI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Admin Router
app.include_router(admin_router)


@app.on_event("startup")
def startup():
    sync_schema(engine)


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class FootprintEntryRequest(BaseModel):
    co2eqkg: int
    note: Optional[str] = "General emission"
    logged_at: Optional[str] = None  # ISO format string or YYYY-MM-DD


class TargetRequest(BaseModel):
    target_co2eqkg: int


@app.get("/")
def root():
    return {"status": "ok", "message": "Backend API is running"}


# ==========================================
# AUTHENTICATION
# ==========================================

@app.post("/api/login")
async def login(request: Request, response: Response):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid request body")

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("username"), str)
        or not isinstance(data.get("password"), str)
    ):
        raise HTTPException(status_code=422, detail="Username and password are required")

    username_input = data["username"].strip()
    password_input = data["password"]

    with engine.connect() as conn:
        user = conn.execute(
            select(users).where(
                or_(users.c.username == username_input, users.c.email == username_input.lower())
            )
        ).mappings().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(password_input, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check status (admin bypasses, user must be approved)
    if user["role"] != "admin" and user["status"] != "approved":
        if user["status"] == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending administrator approval."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account status is: {user['status']}."
        )

    set_session_cookie(response, user["id"])
    return {
        "success": True,
        "id": user["id"],
        "username": user["username"],
        "role": user["role"] or "user",
        "status": user["status"],
    }


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(get_curr_user)):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role") or "user",
        "status": user.get("status") or "approved",
        "co2eqkg": user.get("co2eqkg") or 0,
        "target_co2eqkg": user.get("target_co2eqkg") or 2000,
        "area": user.get("area"),
        "avatar_url": user.get("avatar_url"),
    }


@app.post("/api/register")
async def register(body: RegisterRequest, response: Response):
    username = body.username.strip()
    email = body.email.strip().lower()
    password = body.password

    if len(username) < 3 or len(username) > 50:
        raise HTTPException(status_code=400, detail="Username must be between 3 and 50 characters")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email address format")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    with engine.begin() as conn:
        existing = conn.execute(
            select(users).where(or_(users.c.username == username, users.c.email == email))
        ).mappings().first()

        if existing:
            if existing["username"].lower() == username.lower():
                raise HTTPException(status_code=409, detail="That username is already registered")
            else:
                raise HTTPException(status_code=409, detail="That email is already registered")

        hashed = hash_password(password)
        result = conn.execute(
            insert(users).values(
                username=username,
                email=email,
                password=hashed,
                role="user",
                status="pending",  # Awaits admin approval!
                oauth_provider="local",
                co2eqkg=0,
                target_co2eqkg=2000,
            )
        )
        new_user_id = result.inserted_primary_key[0]

        conn.execute(
            insert(audit).values(
                user_id=new_user_id,
                action="user_registered",
                detail=f"User {username} ({email}) registered. Pending admin approval.",
                created_at=datetime.now(timezone.utc),
            )
        )

    # We do NOT give an active session until approved (or we give session cookie, and get_curr_user checks pending)
    return {
        "success": True,
        "username": username,
        "status": "pending",
        "message": "Account created! Waiting for administrator approval before login.",
    }


# ==========================================
# KPI & FOOTPRINT DASHBOARD
# ==========================================

@app.get("/api/kpi")
def get_kpi(user=Depends(get_curr_user)):
    user_id = user["id"]
    area = user.get("area")
    me_name = user["username"]
    user_target = user.get("target_co2eqkg") or 2000

    with engine.connect() as conn:
        # 1. Total logged kg for this user
        total_sum = conn.execute(
            select(func.coalesce(func.sum(log.c.co2eqkg), 0)).where(log.c.user_id == user_id)
        ).scalar() or 0

        # Sync total with users table if different
        if user.get("co2eqkg") != total_sum and total_sum > 0:
            with engine.begin() as upd_conn:
                upd_conn.execute(
                    update(users).where(users.c.id == user_id).values(co2eqkg=total_sum)
                )

        total_kg = total_sum if total_sum > 0 else (user.get("co2eqkg") or 0)

        # 2. Monthly trend
        month_col = func.strftime("%Y-%m", log.c.logged_at)
        trend_rows = conn.execute(
            select(month_col.label("month"), func.sum(log.c.co2eqkg).label("kg"))
            .where(log.c.user_id == user_id)
            .group_by("month")
            .order_by("month")
        ).mappings().all()

        trend = [{"month": r["month"], "kg": r["kg"]} for r in trend_rows]

        # Calculate percentage change month-over-month
        change_pct = None
        if len(trend) >= 2 and trend[-2]["kg"] and trend[-2]["kg"] > 0:
            last_m = trend[-1]["kg"]
            prev_m = trend[-2]["kg"]
            change_pct = round(((last_m - prev_m) / prev_m) * 100, 1)

        # 3. Recent 20 logs for this user
        recent_rows = conn.execute(
            select(log.c.id, log.c.co2eqkg, log.c.note, log.c.logged_at)
            .where(log.c.user_id == user_id)
            .order_by(log.c.logged_at.desc(), log.c.id.desc())
            .limit(20)
        ).mappings().all()

        recent_logs = [
            {
                "id": r["id"],
                "co2eqkg": r["co2eqkg"],
                "note": r["note"] or "Emission log",
                "logged_at": r["logged_at"].isoformat() if hasattr(r["logged_at"], "isoformat") else str(r["logged_at"]),
            }
            for r in recent_rows
        ]

        # 4. Neighbourhood / Area Leaderboard
        area_rows = []
        if area:
            area_rows = conn.execute(
                select(users.c.username, users.c.co2eqkg)
                .where(users.c.area == area, users.c.status == "approved")
                .order_by(users.c.co2eqkg.asc())
                .limit(50)
            ).mappings().all()
        else:
            # Global leaderboard if no area specified
            area_rows = conn.execute(
                select(users.c.username, users.c.co2eqkg)
                .where(users.c.status == "approved")
                .order_by(users.c.co2eqkg.asc())
                .limit(10)
            ).mappings().all()

        ranked = [
            {
                "rank": i + 1,
                "name": r["username"] if r["username"] == me_name else f"Neighbour {i + 1}",
                "kg": r["co2eqkg"] or 0,
                "you": r["username"] == me_name,
            }
            for i, r in enumerate(area_rows)
        ]
        my_rank = next((r["rank"] for r in ranked if r["you"]), None)
        area_avg = round(sum(r["kg"] for r in ranked) / len(ranked)) if ranked else 0

    return {
        "total_kg": total_kg,
        "target_kg": user_target,
        "change_pct": change_pct,
        "area": area or "Global Community",
        "area_avg_kg": area_avg,
        "rank": my_rank,
        "area_size": len(ranked),
        "leaderboard": ranked[:8],
        "trend": trend,
        "recent_logs": recent_logs,
    }


@app.post("/api/kpi/entry")
def add_footprint_entry(entry: FootprintEntryRequest, user=Depends(get_curr_user)):
    user_id = user["id"]
    if entry.co2eqkg < 0:
        raise HTTPException(status_code=400, detail="CO2 value must be positive")

    log_date = datetime.now(timezone.utc)
    if entry.logged_at:
        try:
            # Handle YYYY-MM-DD or full ISO
            if len(entry.logged_at) == 10:
                log_date = datetime.strptime(entry.logged_at, "%Y-%m-%d")
            else:
                log_date = datetime.fromisoformat(entry.logged_at.replace("Z", "+00:00"))
        except Exception:
            pass

    with engine.begin() as conn:
        res = conn.execute(
            insert(log).values(
                user_id=user_id,
                co2eqkg=entry.co2eqkg,
                note=entry.note or "Emission recorded",
                logged_at=log_date,
            )
        )
        new_entry_id = res.inserted_primary_key[0]

        # Recalculate total footprint
        new_total = conn.execute(
            select(func.sum(log.c.co2eqkg)).where(log.c.user_id == user_id)
        ).scalar() or 0

        conn.execute(
            update(users).where(users.c.id == user_id).values(co2eqkg=new_total)
        )

        conn.execute(
            insert(audit).values(
                user_id=user_id,
                action="log_footprint",
                detail=f"Logged {entry.co2eqkg} kg CO2 ({entry.note})",
                created_at=datetime.now(timezone.utc),
            )
        )

    return {
        "ok": True,
        "entry": {
            "id": new_entry_id,
            "co2eqkg": entry.co2eqkg,
            "note": entry.note,
            "logged_at": log_date.isoformat(),
        },
        "new_total_kg": new_total,
    }


@app.delete("/api/kpi/entry/{entry_id}")
def delete_footprint_entry(entry_id: int, user=Depends(get_curr_user)):
    user_id = user["id"]

    with engine.begin() as conn:
        entry = conn.execute(
            select(log).where(log.c.id == entry_id, log.c.user_id == user_id)
        ).mappings().first()

        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        conn.execute(delete(log).where(log.c.id == entry_id))

        new_total = conn.execute(
            select(func.coalesce(func.sum(log.c.co2eqkg), 0)).where(log.c.user_id == user_id)
        ).scalar() or 0

        conn.execute(
            update(users).where(users.c.id == user_id).values(co2eqkg=new_total)
        )

    return {"ok": True, "deleted_id": entry_id, "new_total_kg": new_total}


@app.post("/api/kpi/target")
def set_kpi_target(body: TargetRequest, user=Depends(get_curr_user)):
    user_id = user["id"]
    if body.target_co2eqkg <= 0:
        raise HTTPException(status_code=400, detail="Target must be greater than 0")

    with engine.begin() as conn:
        conn.execute(
            update(users).where(users.c.id == user_id).values(target_co2eqkg=body.target_co2eqkg)
        )

        conn.execute(
            insert(audit).values(
                user_id=user_id,
                action="update_target",
                detail=f"Set emission target to {body.target_co2eqkg} kg CO2",
                created_at=datetime.now(timezone.utc),
            )
        )

    return {"ok": True, "target_co2eqkg": body.target_co2eqkg}
