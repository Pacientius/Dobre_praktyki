from database.database import engine, SessionLocal
from database.models import Base, Movie, Link, Rating, Tag
import csv

def create_database():
    print("Tworze baze")
    Base.metadata.create_all(engine)
    print("git!")

def load_movies():
    db = SessionLocal()
    with open("files/movies.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            movie = Movie(
                movieId=int(row["movieId"]),
                title=row["title"],
                genres=row["genres"]
            )
            db.add(movie)
        db.commit()
    db.close()


def load_links():
    db = SessionLocal()
    with open("files/links.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            link = Link(
                movieId=int(row["movieId"]),
                imdbId=row["imdbId"],
                tmdbId=row["tmdbId"]
            )
            db.add(link)
        db.commit()
    db.close()


def load_ratings():
    db = SessionLocal()
    with open("files/ratings.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rating = Rating(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                rating=float(row["rating"]),
                timestamp=int(row["timestamp"])
            )
            db.add(rating)
        db.commit()
    db.close()


def load_tags():
    db = SessionLocal()
    with open("files/tags.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tag = Tag(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                tag=row["tag"],
                timestamp=int(row["timestamp"])
            )
            db.add(tag)
        db.commit()
    db.close()


if __name__ == "__main__":
    create_database()
    print("inport")
    load_movies()
    print("inport")    
    load_links()
    print("inport")
    load_ratings()
    print("inport")
    load_tags()
    print("OK")

