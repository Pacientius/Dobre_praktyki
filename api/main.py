from fastapi import FastAPI
from fast_api import *

app = FastAPI()

@app.get("/")
def hello_world():
    return {"hello": "world"}

@app.get("/movies")
def get_movies():
    return load_movies()

@app.get("/links")
def get_links():
    return load_links()

@app.get("/ratings")
def get_ratings():
    return load_ratings()

@app.get("/tags")
def get_tags():
    return load_tags()
