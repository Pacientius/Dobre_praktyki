import sqlite3
import os
import time
import threading
from queue import Queue
import multiprocessing

import random
czas = random.randint(15, 30)


DB_FILE = "tasks.db"

RAM_QUEUE_SIZE = 10
task_queue = Queue(maxsize=RAM_QUEUE_SIZE)

CPU_COUNT = multiprocessing.cpu_count()
THREAD_COUNT = max(1, CPU_COUNT - 1)

LOCK = threading.Lock()

event = threading.Event()


def read_tasks():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM tasks ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_task_status(task_id, status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()


def load_pending_tasks():
    while True:
        if event.is_set():
            break 

        if task_queue.full():
            time.sleep(1)
            continue

        with LOCK:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tasks WHERE status = 'pending' LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                task_id = row[0]
                cursor.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task_id,))
                conn.commit()
                conn.close()
                
                task_queue.put(task_id)
                print(f"[LOADER] Załadowano zadanie {task_id}")
            else:
                conn.close()
                time.sleep(2)
def finish_task(task_id):
    update_task_status(task_id, "done")


def worker():

    import random

    while True:
        try:
            task_id = task_queue.get(timeout=1)
        except:
            time.sleep(1)
            continue

        czas = random.randint(15, 30)

        print(
            f"[WORKER {threading.get_ident()}] Start {task_id} (czas: {czas}s)"
        )

        time.sleep(czas)

        finish_task(task_id)

        print(
            f"[WORKER {threading.get_ident()}] Koniec {task_id} (czas: {czas}s)"
        )

        task_queue.task_done()


        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status != 'done'")
        count = cursor.fetchone()[0]
        conn.close()
        if count == 0:
            print("[WORKER] Wszystkie zadania przetworzone, kończę program.")
            event.set()
            break  



def start_consumer():
    print(f"[CONSUMER] Start z {THREAD_COUNT} workerami i loaderem...")

    threading.Thread(target=load_pending_tasks, daemon=True).start()

    for _ in range(THREAD_COUNT):
        threading.Thread(target=worker, daemon=True).start()

    while not event.is_set():
        time.sleep(1)



#start_consumer()
