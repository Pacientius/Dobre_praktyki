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
    result = []
    for m in movies:
        d = m.__dict__.copy()
        d.pop("_sa_instance_state", None)
        result.append(d)
    db.close()
    return result


@app.get("/movies/{movieId}")
def get_movie(movieId: int):
    db = SessionLocal()
    movie = db.get(Movie, movieId)
    if not movie:
        db.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    result = movie.__dict__.copy()
    result.pop("_sa_instance_state", None)
    db.close()
    return result


@app.post("/movies", status_code=201)
def create_movie(movie: MovieUpdate):
    db = SessionLocal()
    data = movie.model_dump()

    db_movie = Movie(**data)
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)

    result = db_movie.__dict__.copy()
    result.pop("_sa_instance_state", None)
    db.close()
    return result


@app.put("/movies/{movieId}")
def update_movie(movieId: int, movie_data: MovieUpdate):
    db = SessionLocal()
    movie = db.get(Movie, movieId)
    if not movie:
        db.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    data = movie_data.model_dump()

    for key, value in data.items():
        if value is not None:
            setattr(movie, key, value)

    db.commit()
    db.refresh(movie)

    result = movie.__dict__.copy()
    result.pop("_sa_instance_state", None)
    db.close()
    return result


@app.delete("/movies/{movieId}")
def delete_movie(movieId: int):
    db = SessionLocal()
    movie = db.get(Movie, movieId)
    if not movie:
        db.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    db.delete(movie)
    db.commit()
    db.close()
    return {"detail": "Movie deleted"}

@app.get("/links")
def get_links():
    db = SessionLocal()
    items = db.query(Link).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result

@app.get("/links/{movieId}")
def get_link(movieId: int):
    db = SessionLocal()
    link = db.get(Link, movieId)
    if not link:
        db.close()
        raise HTTPException(status_code=404, detail="Link not found")

    result = link.__dict__.copy()
    result.pop("_sa_instance_state", None)
    db.close()
    return result


@app.post("/links", status_code=201)
def create_link(link: LinkUpdate):
    db = SessionLocal()

    db_item = Link(**link.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    result = db_item.__dict__.copy()
    result.pop("_sa_instance_state", None)

    db.close()
    return result


@app.put("/links/{movieId}")
def update_link(movieId: int, data: LinkUpdate):
    db = SessionLocal()
    item = db.get(Link, movieId)
    if not item:
        raise HTTPException(status_code=404, detail="Link not found")

    for key, value in data.dict().items():
        if value is not None:
            setattr(item, key, value)

    db.commit()
    db.refresh(item)

    result = item.__dict__
    result.pop("_sa_instance_state", None)
    db.close()
    return result


@app.delete("/links/{movieId}")
def delete_link(movieId: int):
    db = SessionLocal()
    item = db.get(Link, movieId)
    if not item:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(item)
    db.commit()
    db.close()
    return {"detail": "Link deleted"}


@app.get("/ratings")
def get_ratings():
    db = SessionLocal()
    items = db.query(Rating).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result

@app.get("/ratings/{userId}/{movieId}")
def get_rating(userId: int, movieId: int):
    db = SessionLocal()
    item = db.query(Rating).filter_by(userId=userId, movieId=movieId).first()
    if not item:
        db.close()
        raise HTTPException(status_code=404, detail="Rating not found")

    result = item.__dict__.copy()
    result.pop("_sa_instance_state", None)
    db.close()
    return result

@app.post("/ratings", status_code=201)
def create_rating(rating: RatingUpdate):
    db = SessionLocal()

    db_item = Rating(**rating.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    result = db_item.__dict__.copy()
    result.pop("_sa_instance_state", None)

    db.close()
    return result



@app.put("/ratings/{userId}/{movieId}")
def update_rating(userId: int, movieId: int, data: RatingUpdate):
    db = SessionLocal()
    item = db.query(Rating).filter_by(userId=userId, movieId=movieId).first()
    if not item:
        raise HTTPException(status_code=404, detail="Rating not found")

    for key, value in data.dict().items():
        if value is not None:
            setattr(item, key, value)

    db.commit()
    db.refresh(item)

    result = item.__dict__
    result.pop("_sa_instance_state", None)
    db.close()
    return result


@app.delete("/ratings/{userId}/{movieId}")
def delete_rating(userId: int, movieId: int):
    db = SessionLocal()
    item = db.query(Rating).filter_by(userId=userId, movieId=movieId).first()
    if not item:
        raise HTTPException(status_code=404, detail="Rating not found")

    db.delete(item)
    db.commit()
    db.close()
    return {"detail": "Rating deleted"}

@app.get("/tags")
def get_tags():
    db = SessionLocal()
    items = db.query(Tag).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result

@app.get("/tags/{tagId}")
def get_tag(tagId: int):
    db = SessionLocal()
    item = db.get(Tag, tagId)
    if not item:
        db.close()
        raise HTTPException(status_code=404, detail="Tag not found")

    result = item.__dict__.copy()
    result.pop("_sa_instance_state", None)
    db.close()
    return result

@app.post("/tags", status_code=201)
def create_tag(tag: TagUpdate):
    db = SessionLocal()
    db_item = Tag(**tag.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    result = db_item.__dict__
    result.pop("_sa_instance_state", None)
    db.close()
    return result

@app.post("/tags", status_code=201)
def create_tag(tag: TagUpdate):
    db = SessionLocal()
    db_item = Tag(**tag.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    result = db_item.__dict__
    result.pop("_sa_instance_state", None)
    db.close()
    return result

@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, data: TagUpdate):
    db = SessionLocal()
    item = db.get(Tag, tag_id)
    if not item:
        raise HTTPException(status_code=404, detail="Tag not found")

    for key, value in data.dict().items():
        if value is not None:
            setattr(item, key, value)

    db.commit()
    db.refresh(item)

    result = item.__dict__
    result.pop("_sa_instance_state", None)
    db.close()
    return result


@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int):
    db = SessionLocal()
    item = db.get(Tag, tag_id)
    if not item:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(item)
    db.commit()
    db.close()
    return {"detail": "Tag deleted"}