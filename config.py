import os
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


SERVER_IP = os.getenv("SERVER_IP")
DB_PASS = os.getenv("DB_PASSWORD")   
DB_NAME = os.getenv("DB_NAME")
RABBIT_USER = os.getenv("RABBIT_USER")
RABBIT_PASS = os.getenv("RABBIT_PASSWORD") 


RABBIT_HOST = SERVER_IP
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))

DB_HOST = SERVER_IP
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = "root"



if not DB_PASS:
    print("!!! BŁĄD: Nie wczytano DB_PASSWORD !!!")
else:
    print(f" [OK] Konfiguracja wczytana pomyślnie.")
