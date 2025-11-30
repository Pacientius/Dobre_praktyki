    import pytest
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base, Movie, Link, Rating, Tag
    from api.main import app, get_db

    # -------------------------
    # Ustawienie bazy in-memory
    # -------------------------
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Stwórz wszystkie tabele
    Base.metadata.create_all(bind=engine)

    # -------------------------
    # Override dependency w FastAPI
    # -------------------------
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    # -------------------------
    # Fixtury danych testowych
    # -------------------------
    @pytest.fixture(scope="module", autouse=True)
    def setup_movies():
        db = TestingSessionLocal()
        # dodaj 10 rekordów
        for i in range(1, 11):
            movie = Movie(title=f"Movie {i}", genres="Action")
            db.add(movie)
        db.commit()
        db.close()
        yield
        Base.metadata.drop_all(bind=engine)

    # -------------------------
    # Testy endpointów
    # -------------------------

    def test_get_movies_list():
        res = client.get("/movies")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 10  # powinno być 10 z fixtury
        for i in range(1, 11):
            assert any(m["title"] == f"Movie {i}" for m in data)

    def test_get_movie_single():
        res = client.get("/movies/1")
        assert res.status_code == 200
        movie = res.json()
        assert movie["movieId"] == 1
        assert movie["title"] == "Movie 1"

    def test_get_movie_404():
        res = client.get("/movies/999")
        assert res.status_code == 404

    def test_create_movie():
        payload = {"title": "Test Movie", "genres": "Comedy"}
        res = client.post("/movies/add/", json=payload)
        assert res.status_code == 201
        movie = res.json()
        assert movie["title"] == "Test Movie"
        assert movie["genres"] == "Comedy"
        assert "movieId" in movie

    def test_update_movie():
        payload = {"title": "Updated Movie", "genres": "Drama"}
        res = client.put("/movies/1", json=payload)
        assert res.status_code == 200
        movie = res.json()
        assert movie["title"] == "Updated Movie"
        assert movie["genres"] == "Drama"

    def test_delete_movie():
        res = client.delete("/movies/2")
        assert res.status_code == 200
        # GET po usunięciu → 404
        res2 = client.get("/movies/2")
        assert res2.status_code == 404

    # -------------------------
    # Testy CRUD dla innych modeli
    # -------------------------
    def test_link_crud():
        # CREATE
        created = client.post("/links", json={"movieId": 1, "imdbId": "tt111", "tmdbId": "123"}).json()
        lid = created["movieId"]
        # READ
        res = client.get(f"/links/{lid}")
        assert res.status_code == 200
        assert res.json()["imdbId"] == "tt111"
        # UPDATE
        client.put(f"/links/{lid}", json={"imdbId": "tt222"})
        updated = client.get(f"/links/{lid}").json()
        assert updated["imdbId"] == "tt222"
        # DELETE
        client.delete(f"/links/{lid}")
        res2 = client.get(f"/links/{lid}")
        assert res2.status_code == 404

    def test_rating_crud():
        # CREATE
        created = client.post("/ratings", json={"userId": 1, "movieId": 1, "rating": 4.5, "timestamp": 123})
        assert created.status_code == 201
        # READ
        res = client.get("/ratings/1/1")
        assert res.status_code == 200
        assert res.json()["rating"] == 4.5
        # UPDATE
        client.put("/ratings/1/1", json={"rating": 3.0})
        updated = client.get("/ratings/1/1").json()
        assert updated["rating"] == 3.0
        # DELETE
        client.delete("/ratings/1/1")
        res2 = client.get("/ratings/1/1")
        assert res2.status_code == 404

    def test_tag_crud():
        # CREATE
        created = client.post("/tags", json={"userId": 1, "movieId": 1, "tag": "Fun", "timestamp": 123}).json()
        tid = created["id"]
        # READ
        res = client.get(f"/tags/{tid}")
        assert res.status_code == 200
        assert res.json()["tag"] == "Fun"
        # UPDATE
        client.put(f"/tags/{tid}", json={"tag": "Serious"})
        updated = client.get(f"/tags/{tid}").json()
        assert updated["tag"] == "Serious"
        # DELETE
        client.delete(f"/tags/{tid}")
        res2 = client.get(f"/tags/{tid}")
        assert res2.status_code == 404
