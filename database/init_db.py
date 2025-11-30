import os
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from .models import Movie, Link, Rating, Tag
import csv

DB_PATH = "./database/DATA.db"

def load_csv_to_table(session: Session, table_class, file_path, columns_map):
    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items = []
        for row in reader:
            data = {col: row[csv_col] for col, csv_col in columns_map.items()}
            items.append(table_class(**data))
        session.add_all(items)
        session.commit()

def init_db():
    if os.path.exists(DB_PATH):
        print("Baza już istnieje")
        return


    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        load_csv_to_table(db, Movie, "files/movies.csv", {"movieId": "movieId", "title": "title", "genres": "genres"})
        load_csv_to_table(db, Link, "files/links.csv", {"movieId": "movieId", "imdbId": "imdbId", "tmdbId": "tmdbId"})
        load_csv_to_table(db, Rating, "files/ratings.csv", {"userId": "userId", "movieId": "movieId", "rating": "rating", "timestamp": "timestamp"})
        load_csv_to_table(db, Tag, "files/tags.csv", {"userId": "userId", "movieId": "movieId", "tag": "tag", "timestamp": "timestamp"})
        print("Baza danych zainportowana.")
    finally:
        db.close()
