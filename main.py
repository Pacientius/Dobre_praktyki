from fastapi import FastAPI

from database.database import get_db, engine, Base
from endpoints import users

app = FastAPI()


Base.metadata.create_all(bind=engine)


@app.get("/")
async def hello():
    return {"message": "Hello World"}
    tags=["Hello"]


app.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)

@app.get("login")
async def login():
    return {"message": "Login endpoint"}