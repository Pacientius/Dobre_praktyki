from fastapi.testclient import TestClient
from api.main import app

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
