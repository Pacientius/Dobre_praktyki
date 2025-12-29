import mysql.connector
import config

def init():
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        cursor = conn.cursor()
        
        query = """
            CREATE TABLE IF NOT EXISTS detections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                image_url TEXT,
                people_count INT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        cursor.execute(query)
        conn.commit()
        print(" [v] Sukces: Baza danych i tabela 'detections' są gotowe.")
        
    except Exception as e:
        print(f" [!] Błąd inicjalizacji bazy: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init()
