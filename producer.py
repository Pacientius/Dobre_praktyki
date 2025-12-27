import sqlite3
import os

DB_FILE = "tasks.db"


def ensure_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                status TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()


def add_task():
    ensure_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(id) FROM tasks")
    result = cursor.fetchone()
    new_id = (result[0] or 0) + 1
    
    cursor.execute("INSERT INTO tasks (id, status) VALUES (?, ?)", (new_id, "pending"))
    conn.commit()
    conn.close()
    
    print(f"[PRODUCER] Dodano zadanie {new_id}")


def add_tasks_bulk(count):
    ensure_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(id) FROM tasks")
    result = cursor.fetchone()
    start_id = (result[0] or 0) + 1
    
    tasks = [(start_id + i, "pending") for i in range(count)]
    cursor.executemany("INSERT INTO tasks (id, status) VALUES (?, ?)", tasks)
    conn.commit()
    conn.close()
    
    print(f"[PRODUCER] Dodano {count} zadań")


if __name__ == "__main__":
    add_task()
