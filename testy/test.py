import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database.models import Base, Movie, Link, Rating, Tag
from main import app
from endpoints.movies import get_db as movies_get_db
from endpoints.links import get_db as links_get_db
from endpoints.ratings import get_db as ratings_get_db
from endpoints.tags import get_db as tags_get_db

@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Testingsesionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = Testingsesionlocal()
    for i in range(1, 11):
        db.add(Movie(movieId=i, title=f"Movie {i}", genres="Genre"))
    for i in range(1, 11):
        db.add(Link(movieId=i, imdbId=1000 + i, tmdbId=10000 + i))
    for i in range(1, 11):
        db.add(Rating(userId=i, movieId=i, rating=4.0, timestamp=1620000000 + i))
    for i in range(1, 11):
        db.add(Tag(userId=i, movieId=i, tag=f"Tag {i}", timestamp=1620000000 + i))
    db.commit()
    yield Testingsesionlocal
    db.close()
    engine.dispose()

@pytest.fixture
def client(test_db):
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[movies_get_db] = override_get_db
    app.dependency_overrides[links_get_db] = override_get_db
    app.dependency_overrides[ratings_get_db] = override_get_db
    app.dependency_overrides[tags_get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_movies(client):
    response = client.get("/movies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10

def test_get_single_movie(client):
    response = client.get("/movies/1")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Movie 1"

def test_create_movie(client):
    new_movie = {"title": "Movie 11", "genres": "Genre11"}
    response = client.post("/movies/", json=new_movie)
    assert response.status_code == 201
    data = response.json()
    assert data["movieId"] == 11

    response = client.get("/movies")
    assert len(response.json()) == 11

def test_update_movie_partial(client):
    update_data = {"title": "Updated Movie 1"}
    response = client.put("/movies/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Movie 1"
    assert data["genres"] == "Genre"  

def test_delete_movie(client):
    response = client.delete("/movies/1")
    assert response.status_code == 204

    response = client.get("/movies/1")
    assert response.status_code == 404

#--------------------------------------------------------------------------------


def test_get_links(client):
    response = client.get("/links/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10

def test_get_single_link(client):
    response = client.get("/links/1")
    assert response.status_code == 200
    data = response.json()
    assert data["movieId"] == 1

def test_create_link(client):
    new_link = {"movieId": 11, "imdbId": 1000, "tmdbId": 10000}
    response = client.post("/links/", json=new_link)
    assert response.status_code == 201
    data = response.json()
    assert data["movieId"] == 11

def test_update_link_partial(client):
    update_data = {"imdbId": 2000}
    response = client.put("/links/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["imdbId"] == 2000
    assert data["tmdbId"] == 10001

def test_delete_link(client):
    response = client.delete("/links/1")
    assert response.status_code == 204

    response = client.get("/links/1")
    assert response.status_code == 404


#--------------------------------------------------------------------------------

def test_get_ratings(client):
    response = client.get("/ratings/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10 

def test_get_single_rating(client):
    response = client.get("/ratings/1")
    assert response.status_code == 200
    data = response.json()
    assert data["userId"] == 1

def test_create_rating(client):
    new_rating = {"userId": 11, "movieId": 1, "rating": 4.5, "timestamp": 1620000000}
    response = client.post("/ratings/", json=new_rating)
    assert response.status_code == 201
    data = response.json()
    assert data["userId"] == 11

def test_update_rating_partial(client):
    update_data = {"rating": 3.5}
    response = client.put("/ratings/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 3.5
    assert data["timestamp"] == 1620000001

def test_delete_rating(client):
    response = client.delete("/ratings/1")
    assert response.status_code == 204

    response = client.get("/ratings/1")
    assert response.status_code == 404
#--------------------------------------------------------------------------------

def test_get_tags(client):
    response = client.get("/tags/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10

def test_get_single_tag(client):
    response = client.get("/tags/1")
    assert response.status_code == 200
    data = response.json()
    assert data["userId"] == 1

def test_create_tag(client):
    new_tag = {"userId": 11, "movieId": 1, "tag": "Great Movie", "timestamp": 1620000000}
    response = client.post("/tags/", json=new_tag)
    assert response.status_code == 201
    data = response.json()
    assert data["userId"] == 11

def test_update_tag_partial(client):
    update_data = {"tag": "Updated Tag"}
    response = client.put("/tags/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["tag"] == "Updated Tag"
    assert data["timestamp"] == 1620000001 

def test_delete_tag(client):
    response = client.delete("/tags/1")
    assert response.status_code == 204

    response = client.get("/tags/1")
    assert response.status_code == 404