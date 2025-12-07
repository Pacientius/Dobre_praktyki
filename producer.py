import csv
import os

FILE = "tasks.csv"


def ensure_file():
    if not os.path.exists(FILE):
        with open(FILE, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "status"])


def add_task():
    ensure_file()

    with open(FILE, "r") as f:
        rows = list(csv.reader(f))

    if len(rows) <= 1:
        new_id = 1
    else:
        last_id = int(rows[-1][0])
        new_id = last_id + 1

    with open(FILE, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow([new_id, "pending"])

    print(f"[PRODUCER] Dodano zadanie {new_id}")


add_task()
