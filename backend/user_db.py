from pathlib import Path
from sqlalchemy import create_engine,event

DB_PATH = Path(__file__).resolve().parent / "app.db"

engine = create_engine(f"sqlite:///{DB_PATH}",connect_args={"check_same_thread":False},)

@event.listens_for(engine,"connect")
def enable_fk(dbapi_conn,_):
    dbapi_conn.execute("PRAGMA foreign_keys=ON") # ignore fk unless told not to

