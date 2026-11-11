from fastapi import FastAPI, HTTPException, Request,Response,Cookie,status
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime, timedelta, timezone
from user_db import engine
from models import tables
from Auth_manager import verify_password
from sqlalchemy import select
from pydantic import BaseModel
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from Auth_manager import COOKIE_NAME, get_curr_user, set_session_cookie, verify_password
import datetime



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from models import sync_schema

@app.on_event("startup")
def startup():
    sync_schema(engine)

@app.get("/")
def hello():
    return {"message": "hi"}



    


users = tables["users"]

@app.post("/api/login")
async def login(request: Request,response:Response):
    try:
        data = await request.json()
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid request body")

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("username"), str)
        or not isinstance(data.get("password"), str)
    ):
        raise HTTPException(status_code=422, detail="Username and password are required")

    with engine.connect() as conn:
        user = conn.execute(
            select(users).where(
                users.c.username == data["username"]
            )
        ).mappings().first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        data["password"],
        user["password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    set_session_cookie(response,user["id"])
    return {
        "success": True,
        "username": user["username"]
    }

@app.post("/api/logout")
def logout(reponse:Response):
    response.delete_cookie(COOKIE_NAME,path = "/")
    return {"ok":True}

@app.get("/api/me")
def me(user = Depends(get_curr_user)):
    return {"id": user["id"], "username": user["username"], "role": user["role"] or "user"}


log = tables["footprint_log"]

@app.get("/api/kpi")
def kpi(user=Depends(get_curr_user)):
    area,me = user["area"],user["username"]

    with engine.connect()as conn:
        rows=[]
        if area:
            rows = conn.execute(
                select(users.c.username, users.c.co2eqkg)
                .where(users.c.area == area, users.c.co2eqkg.is_not(None))
                .order_by(users.c.co2eqkg)   # lowest footprint = rank 1
                .limit(100)
            ).mappings().all()
        month = func.strfttime("%Y-%m",log.c.logged_at)
        trend = conn.execute(select(month.label("month"),func.sum(log.c.co2eqkg).label("kg"))
        .where(log.c.user_id == user["id"]) .group_by(month).order_by(month)                     
        ).mappings().all

    ranked = [ {"rank": i +1,"kg":r["co2eqkg"],"you":r["username"]== me,
                "name":me if r["username"]== me else f"Neighbour {i+1}"}
                for i ,r in enumerate(rows)]
    my_rank = next((r["rank"] for r in ranked if r["you"]),None)
    top = ranked[:5] +([r for r in ranked if r["you"]]if my_rank and my_rank > 5 else [])
    change = None
    if len(trend) >=2 and trend[-2]["kg"]:
        change = round((trend[-1]["kg"] - trend [-2]["kg"]/ trend[-2]["kg"] * 100, 1))
    return {
        "total_kg": user["co2eqkg"] or 0,
        "change_pct": change,
        "area": area,
        "area_avg_kg": round(sum(r["kg"] for r in ranked) / len(ranked)) if ranked else 0,
        "rank": my_rank,
        "area_size": len(ranked),
        "leaderboard": top,
        "trend": [dict(t) for t in trend],
    }