from fastapi import FastAPI
from database.init_db import init_db
from endpoints.movies import router as movies_router
from endpoints.ratings import router as ratings_router
from endpoints.tags import router as tags_router
from endpoints.links import router as links_router
app = FastAPI()


@app.on_event("startup")
def on_startup():
    init_db()  

@app.get("/")
def root():
    return {"hello": "world"}

app.include_router(movies_router)
app.include_router(links_router)
app.include_router(ratings_router)
app.include_router(tags_router)
