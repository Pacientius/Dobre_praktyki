from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from pydantic import BaseModel


class Movie(Base):
    __tablename__ = "movies"
    movieId = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    genres = Column(String, nullable=True)

    links = relationship("Link", back_populates="movie")
    ratings = relationship("Rating", back_populates="movie")
    tags = relationship("Tag", back_populates="movie")

class MovieCreate(BaseModel):
    title: str
    genres: str

class MovieRead(BaseModel):
    movieId: int
    title: str
    genres: str

    class Config:
        orm_mode = True

class MovieUpdate(BaseModel):
    title: str | None = None
    genres: str | None = None

class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    movieId = Column(Integer, ForeignKey("movies.movieId"))
    imdbId = Column(Integer)
    tmdbId = Column(Integer)
    movie = relationship("Movie", back_populates="links")

class LinkCreate(BaseModel):
    movieId: int
    imdbId: int
    tmdbId: int

class LinkUpdate(BaseModel):
    imdbId: int | None = None
    tmdbId: int | None = None

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer)
    movieId = Column(Integer, ForeignKey("movies.movieId"))
    rating = Column(Float)
    timestamp = Column(Integer)
    movie = relationship("Movie", back_populates="ratings")

class RatingCreate(BaseModel):
    userId: int
    movieId: int
    rating: float
    timestamp: int

class RatingUpdate(BaseModel):
    rating: float | None = None
    timestamp: int | None = None


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer)
    movieId = Column(Integer, ForeignKey("movies.movieId"))
    tag = Column(String)
    timestamp = Column(Integer)
    movie = relationship("Movie", back_populates="tags")

class TagCreate(BaseModel):
    userId: int
    movieId: int
    tag: str
    timestamp: int

class TagUpdate(BaseModel):
    tag: str | None = None
    timestamp: int | None = None