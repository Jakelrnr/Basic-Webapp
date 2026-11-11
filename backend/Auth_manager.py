import bcrypt
import os
from datetime import datetime, timedelta, timezone

import jwt  # pip install pyjwt
from fastapi import Cookie, HTTPException, Response, status
from sqlalchemy import select

from models import tables
from user_db import engine

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")        # str, so SQLite can store it

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


SECRET_KEY = os.environ.get("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("Key is broken champ")
COOKIE_NAME = "session"
users = tables["users"]

def set_session_cookie(response:Response,user_id:int) -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=1)},
        SECRET_KEY, algorithm="HS256",)
    response.set_cookie(key=COOKIE_NAME,value=token,httponly=True,samesite="strict",max_age=3600,path="/",secure=os.environ.get("COOKIE_SECURE","0")=="1",)

    
def get_curr_user(session_token:str |None = Cookie(default= None,alias=COOKIE_NAME))->dict:
   err = HTTPException(status.HTTP_401_UNAUTHORIZED,"not logged in :O")
   if not session_token :
       raise err
   try:
        user_id=(jwt.decode(session_token,SECRET_KEY,algorithms = ["HS256"])["sub"])
   except (jwt.PyJWTError,KeyError,ValueError):
        raise err
   with engine.connect() as conn:
        row = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
   if row is None:
        raise err
   return {k: v for k, v in row.items() if k != "password"}