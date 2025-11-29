from fastapi import *
from database.database import SessionLocal
from database.models import *

app = FastAPI()

@app.get("/")
def root():
    return {"hello": "world"}

@app.get("/movies")
def get_movies():
    db = SessionLocal()
    movies = db.query(Movie).all()
    result = [m.__dict__ for m in movies]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result


@app.get("/links")
def get_links():
    db = SessionLocal()
    items = db.query(Link).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result


@app.get("/ratings")
def get_ratings():
    db = SessionLocal()
    items = db.query(Rating).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result


@app.get("/tags")
def get_tags():
    db = SessionLocal()
    items = db.query(Tag).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result
