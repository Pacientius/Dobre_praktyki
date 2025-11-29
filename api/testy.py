#from fastapi.testclient import TestClient
#import sys
#import os

# Dodaj folder projektu do sys.path, żeby Python znalazł moduł api
#sys.path.append(os.path.abspath("C:/Users/hubgr/Desktop/Studia/dobre_praktyki_programowania"))

# Teraz importujemy FastAPI app z main.py
#from api.main import app

#client = TestClient(app)

from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}


def test_movies_endpoint():
    response = client.get("/movies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  

def test_links_endpoint():
    response = client.get("/links")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ratings_endpoint():
    response = client.get("/ratings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tags_endpoint():
    response = client.get("/tags")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
