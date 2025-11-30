from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Baza produkcyjna (plik SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./movies.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Funkcja do testów w pamięci ---
def get_test_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    return TestingSessionLocal()
