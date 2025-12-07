import csv
import os
import time
import threading
from queue import Queue
import multiprocessing

import random
czas = random.randint(15, 30)


FILE = "tasks.csv"

RAM_QUEUE_SIZE = 10
task_queue = Queue(maxsize=RAM_QUEUE_SIZE)

CPU_COUNT = multiprocessing.cpu_count()
THREAD_COUNT = max(1, CPU_COUNT - 1)

LOCK = threading.Lock()


def read_tasks():
    with open(FILE, "r") as f:
        return list(csv.reader(f))


def write_tasks(rows):
    with open(FILE, "w", newline="") as f:
        csv.writer(f).writerows(rows)


def load_pending_tasks():
    while True:
        if task_queue.full():
            time.sleep(1)
            continue

        with LOCK:
            rows = read_tasks()
            added = False

            for i in range(1, len(rows)):
                task_id, status = rows[i]
                if status == "pending":
                    rows[i][1] = "in_progress"
                    write_tasks(rows)

                    task_queue.put((task_id, i))
                    print(f"[LOADER] Załadowano zadanie {task_id} do RAM")
                    added = True
                    break

        if not added:
            time.sleep(2)


def finish_task(row_index):
    with LOCK:
        rows = read_tasks()
        rows[row_index][1] = "done"
        write_tasks(rows)


def worker():

    import random

    while True:
        try:
            task_id, row_index = task_queue.get(timeout=1)
        except:
            time.sleep(1)
            continue

        czas = random.randint(15, 30)

        print(
            f"[WORKER {threading.get_ident()}] Start zadania {task_id} (czas: {czas}s)"
        )

        time.sleep(czas)

        finish_task(row_index)

        print(
            f"[WORKER {threading.get_ident()}] Koniec zadania {task_id} (czas: {czas}s)"
        )

        task_queue.task_done()



def start_consumer():
    print(f"[CONSUMER] Start z {THREAD_COUNT} workerami i loaderem...")

    threading.Thread(target=load_pending_tasks, daemon=True).start()

    for _ in range(THREAD_COUNT):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        time.sleep(1)



start_consumer()
