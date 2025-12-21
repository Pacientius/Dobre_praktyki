# main.py
import subprocess
import sys
import time
from consumer import start_consumer


def produce_100_tasks():
    print("[MAIN] Generuję.")
    for x in range(100):
        subprocess.run([sys.executable, "producer.py"])

    print("[MAIN] Dodano")

"""
try:
    subprocess.run([sys.executable, "duzo.py"], check=True)
except subprocess.CalledProcessError as e:
    print(f"[MAIN] Błąd podczas uruchamiania duzo.py: {e}")
"""

produce_100_tasks()

print("[MAIN] Uruchamiam consumerów...")
start_consumer()
