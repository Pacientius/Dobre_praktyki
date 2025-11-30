from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"

    movieId = Column(Integer, primary_key=True)
    title = Column(String)
    genres = Column(String)

class MovieUpdate(BaseModel):
    title: str | None = None
    genres: str | None = None

class Link(Base):
    __tablename__ = "links"

    movieId = Column(Integer, primary_key=True)
    imdbId = Column(String)
    tmdbId = Column(String)

class LinkUpdate(BaseModel):
    imdbId: str | None = None
    tmdbId: str | None = None

class Rating(Base):
    __tablename__ = "ratings"

    userId = Column(Integer, primary_key=True)
    movieId = Column(Integer, primary_key=True) 
    rating = Column(Float)
    timestamp = Column(Integer)
    
class RatingUpdate(BaseModel):
    userId: int  | None = None
    movieId: int | None = None
    rating: float| None = None
    timestamp: int| None = None

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)  
    userId = Column(Integer)
    movieId = Column(Integer)
    tag = Column(String)
    timestamp = Column(Integer)


class TagUpdate(BaseModel):
    id: int | None = None
    userId: int | None = None
    movieId: int | None = None
    tag: str | None = None
    timestamp: int | None = None