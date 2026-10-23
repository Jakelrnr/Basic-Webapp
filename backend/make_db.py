from user_db import engine
from models import sync_schema

sync_schema(engine)
print("done")