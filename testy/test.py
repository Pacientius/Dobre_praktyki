from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}



def test_movies_create():
    data = {
        "title": "Movie TEST",
        "genres": "Action"
    }
    response = client.post("/movies", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Movie TEST"
    assert body["genres"] == "Action"
    global MOVIE_ID
    MOVIE_ID = body["movieId"]


def test_movies_read_single():
    response = client.get(f"/movies/{MOVIE_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["movieId"] == MOVIE_ID


def test_movies_update():
    data = {"title": "UPDATED MOVIE"}
    response = client.put(f"/movies/{MOVIE_ID}", json=data)
    assert response.status_code == 200
    assert response.json()["title"] == "UPDATED MOVIE"


def test_movies_delete():
    response = client.delete(f"/movies/{MOVIE_ID}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Movie deleted"}



def test_links_create():
    data = {
        "imdbId": "tt1234567",
        "tmdbId": "99999"
    }
    response = client.post("/links", json=data)
    assert response.status_code == 201
    body = response.json()
    global LINK_ID
    LINK_ID = body["movieId"]


def test_links_read_single():
    response = client.get(f"/links/{LINK_ID}")
    assert response.status_code == 200
    assert response.json()["movieId"] == LINK_ID


def test_links_update():
    data = {"imdbId": "tt7654321"}
    response = client.put(f"/links/{LINK_ID}", json=data)
    assert response.status_code == 200
    assert response.json()["imdbId"] == "tt7654321"


def test_links_delete():
    response = client.delete(f"/links/{LINK_ID}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Link deleted"}



def test_ratings_create():
    data = {
        "userId": 1,
        "movieId": 100,
        "rating": 4.5,
        "timestamp": 123456
    }
    response = client.post("/ratings", json=data)
    assert response.status_code == 201
    global R_USER, R_MOVIE
    R_USER = 1
    R_MOVIE = 100


def test_ratings_read_single():
    response = client.get(f"/ratings/{R_USER}/{R_MOVIE}")
    assert response.status_code == 200
    assert response.json()["rating"] == 4.5


def test_ratings_update():
    data = {"rating": 3.0}
    response = client.put(f"/ratings/{R_USER}/{R_MOVIE}", json=data)
    assert response.status_code == 200
    assert response.json()["rating"] == 3.0


def test_ratings_delete():
    response = client.delete(f"/ratings/{R_USER}/{R_MOVIE}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Rating deleted"}



def test_tags_create():
    data = {
        "userId": 2,
        "movieId": 200,
        "tag": "cool",
        "timestamp": 987654
    }
    response = client.post("/tags", json=data)
    assert response.status_code == 201
    global TAG_ID
    TAG_ID = response.json()["id"]


def test_tags_read_single():
    response = client.get(f"/tags/{TAG_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == TAG_ID


def test_tags_update():
    data = {"tag": "UPDATED_TAG"}
    response = client.put(f"/tags/{TAG_ID}", json=data)
    assert response.status_code == 200
    assert response.json()["tag"] == "UPDATED_TAG"


def test_tags_delete():
    response = client.delete(f"/tags/{TAG_ID}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Tag deleted"}
