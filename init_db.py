import mysql.connector
import config
from mysql.connector.aio import connect
import time 


#robinbie bazy i tabel 
async def init_db():
    conn = None
    for i in range(10):
        try:
            conn = mysql.connector.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASS
            )
            if conn.is_connected():
                print(f" [v] Połączono z serwerem MySQL (Próba {i+1}).")
                break
        except mysql.connector.Error as e:
            print(f" [!] Czekam na MySQL... ({e}). Próba {i+1}/10...")
            time.sleep(5)
    else:
        raise Exception("Nie udało się połączyć z bazą danych.")



    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
        cursor.execute(f"USE {config.DB_NAME}")
        
        query = """
            CREATE TABLE IF NOT EXISTS detections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(36),
                image_url TEXT,
                people_count INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        cursor.execute(query)
        conn.commit()
        print(f" [v] Sukces: Baza '{config.DB_NAME}' i tabela 'detections' są gotowe.")
        
    except Exception as e:
        print(f" [!] Błąd inicjalizacji bazy: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_db()
