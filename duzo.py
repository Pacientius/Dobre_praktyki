import csv
import os

FILE = "tasks.csv"
NUM_TASKS = 10000

with open(FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "status"]) 
    for i in range(1, NUM_TASKS + 1):
        writer.writerow([i, "pending"])

print(f"[PRODUCER] Stworzono {NUM_TASKS} zadań")
