from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from user_db import engine
from models import tables
from Auth_manager import verify_password
from sqlalchemy import select
from pydantic import BaseModel
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

@app.get("/user")
def add_user(username, password):
    pass

    


users = tables["users"]

@app.post("/api/login")
async def login(request: Request):
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

    return {
        "success": True,
        "username": user["username"]
    }