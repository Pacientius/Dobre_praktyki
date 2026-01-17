from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from contextlib import asynccontextmanager
import config  
from init_db import init_db

app = FastAPI(title="Service A - Zapisywanie od bazy danych")

class DetectionResult(BaseModel):
    uid: str
    url: str
    count: int

class OCRResult(BaseModel):
    uid: str
    url: str
    plate_number: str

def get_db_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME,
        connect_timeout=10
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(" [Serwis A] Sprawdzanie i inicjalizacja bazy danych")
    try:
        await init_db()
        print(" [Serwis A] Gotowy do odbierania danych.")
        yield
    except Exception as e:
        print(f" [!] Błąd krytyczny podczas inicjalizacji: {e}")
        import os
        print(" [Serwis A] Wyłączanie serwisu...")
        os._exit(1)
    finally:
        print(" [Serwis A] Wyłączanie serwisu...")




app = FastAPI(title="Service A - Result Receiver", lifespan=lifespan)





@app.post("/save", status_code=201)
async def save_result(payload: DetectionResult):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO detections (uid, image_url, people_count) 
            VALUES (%s, %s, %s)
        """
        values = (payload.uid, payload.url, payload.count)

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        return {"status": "success", "data": {"uuid": payload.uid, "url": payload.url, "count": payload.count}}
        

        
    except mysql.connector.Error as err:
        print(f" [!] Błąd połączenia z bazą danych MySQL: {err}")
        raise HTTPException(status_code=500, detail=f"Błąd połączenia z bazą danych: {err}")

    except mysql.connector.Error as err:
        print(f" [!] Błąd bazy danych MySQL: {err}")
        raise HTTPException(status_code=500, detail=f"Błąd bazy danych: {err}")
    except Exception as e:
        print(f" [!] Nieoczekiwany błąd: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.post("/save_ocr", status_code=201)
async def save_ocr_result(payload: OCRResult):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO ocr_results (uid, image_url, plate_number) 
            VALUES (%s, %s, %s)
        """
        values = (payload.uid, payload.url, payload.plate_number)

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        return {"status": "success", "data": {"uuid": payload.uid, "url": payload.url, "plate_number": payload.plate_number}}
        
    except mysql.connector.Error as err:
        print(f" [!] Błąd bazy danych MySQL: {err}")
        raise HTTPException(status_code=500, detail=f"Błąd bazy danych: {err}")
    except Exception as e:
        print(f" [!] Nieoczekiwany błąd: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        if conn.is_connected():
            conn.close()
            return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}, 503
