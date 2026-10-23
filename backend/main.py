from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "hi"}

@app.get("/user")
def add_user(username, email, password):
    pass
    