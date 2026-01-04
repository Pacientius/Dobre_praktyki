import redis
import json
import time
import uuid
import httpx
import cv2
import numpy as np
import urllib.request
import config
from tenacity import retry, wait_exponential, stop_after_attempt
import os
import urllib.request
from urllib.parse import urlparse

QUEUE_MAIN = "AI_queue"
QUEUE_PROCESSING = "AI_queue_temp"

SERVICE_A_URL = f"http://{config.SERVICE_A_HOST}:{config.SERVICE_A_PORT}/save"

#temp
count = 1
x=0



#AI

hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def detect_people(url: str) -> int:
    if not is_valid_url(url):
        print(f" [!] Błąd: To nie jest poprawny URL: {url}")
        return 0

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.info().get_content_type()
            if not content_type.startswith('image/'):
                print(f" [!] Błąd: URL nie prowadzi do obrazu (Typ: {content_type})")
                return 0
                
            image_np = np.asarray(bytearray(resp.read()), dtype="uint8")
            
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if img is None:
            print(" [!] Błąd: Nie udało się zdekodować obrazu")
            return 0

        height, width = img.shape[:2]
        img = cv2.resize(img, (1280, int(height * (1280 / width))))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        boxes, weights = hog.detectMultiScale(
            gray,
            winStride=(4, 4),
            padding=(8, 8),
            scale=1.1,
            hitThreshold=-0.5,
        )

        rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        pick = cv2.dnn.NMSBoxes(
            rects.tolist(),
            [float(w) for w in weights],
            score_threshold=0.4,
            nms_threshold=0.6,
        )

        return len(pick) if len(pick) > 0 else 0

    except Exception as e:
        print(f" [!] AI error: {e}")
        return 0












#siec



@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True,
)
def send_result(task_id: str, url: str, count: int):
    payload = {
        "uid": task_id,
        "url": url,
        "count": count,
    }
    with httpx.Client(timeout=10) as client:
        response = client.post(SERVICE_A_URL, json=payload)
        response.raise_for_status()

    




def update_status(r: redis.Redis, task_id: str, status: str, url: str, count=None):
    print(" Aktualizacja statusu zadania w Redisie")
    data = {
        "id": task_id,
        "status": status,
        "url": url,
        "updated_at": time.asctime(),
    }
    if count is not None:
        data["count"] = count

    r.set(task_id, json.dumps(data), ex=1200) #3600 godzina

#uwuanie dziwnych statusow zadan
def get_task_status(r: redis.Redis, task_id: str) -> str:
    data = r.get(task_id)
    if not data:
        r.rpop (task_id)
        return "not_found"


def start_consumer():  
    print(" [*] Consumer started")

    r = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True,
    )
    print (" [*] Połączono z Redisem")

    while True:

        task_id = r.brpoplpush(
            QUEUE_MAIN, 
            QUEUE_PROCESSING,
            timeout=0,
            )

        if task_id is None:
            print(" [*] Kolejka pusta. Zamykanie.")
            os._exit(0)



        try:
            if not r.exists(task_id):
                print(f" [!] Zadanie {task_id} wygasło lub usunięte. Usuwam z {QUEUE_PROCESSING}.")
                r.lrem(QUEUE_PROCESSING, 1, task_id)
                continue

            
            #data = r.hgetall(task_id)
            data = json.loads(r.get(task_id))
            task_id = data["id"]
            url = data["url"]
            status= data["status"]


            #czy zły url
            if not is_valid_url(url):
                raise ValueError(f"Nieprawidłowy URL: {url}")
            
            if status == "done":
                    print(" [i] Zadanie już oznaczone jako done pomijam aktualizację statusu.")
                    

            elif status != "done":
                    count = detect_people(url)
                    update_status(r, task_id, "done", url, count)

            send_result(task_id, url, count)
            r.lrem(QUEUE_PROCESSING, 1, task_id)
            r.delete(task_id)
            print(f" [✓] Task {task_id} done and removed from processing") 

        
        except (ValueError, json.JSONDecodeError) as e:
            print(f" [!] Błąd krytyczny usuwam zadanie: {e}")
            r.lrem(QUEUE_PROCESSING, 1, task_id)
            r.delete(task_id)

        except Exception as e:
            print(f"[!]erooroooo: {e}")
            r.lpush(QUEUE_MAIN, task_id)
            r.lrem(QUEUE_PROCESSING, 1, task_id)
            time.sleep(5)
        


if __name__ == "__main__":
    start_consumer()
