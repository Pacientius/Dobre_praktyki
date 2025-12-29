import pika
import json
import cv2
import numpy as np
import urllib.request
import mysql.connector
import config

hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def save_to_db(url, count):
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        cursor = conn.cursor()
        query = "INSERT INTO detections (image_url, people_count) VALUES (%s, %s)"
        cursor.execute(query, (url, count))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f" [!] Błąd zapisu do bazy: {e}")


def detect_people(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        image_np = np.asarray(bytearray(resp.read()), dtype="uint8")
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if img is None:
            print(" [!] Nie udało się wczytać obrazu")
            return 0

        img = cv2.resize(img, (1280, int(img.shape[0] * 1280 / img.shape[1])))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


        boxes, weights = hog.detectMultiScale(
            gray,
            winStride=(4, 4),
            padding=(8, 8),
            scale=1.1,
            hitThreshold=-0.5
        )

        boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])


        rects = [b.tolist() for b in boxes]
        pick = cv2.dnn.NMSBoxes(rects, [float(w) for w in weights], score_threshold=0.4, nms_threshold=0.6)
        person_count = len(pick) if pick is not None else 0

        print(f" [*] Znaleziono osób: {person_count}")











        return person_count

    except Exception as e:
        print(f" [!] Błąd detekcji: {e}")
        return 0

def callback(ch, method, properties, body):
    data = json.loads(body)
    url = data['url']
    print(f" [*] Przetwarzanie: {url}")

    count = detect_people(url)
    save_to_db(url, count)

    print(f" [v] Gotowe. Znaleziono osób: {count}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    credentials = pika.PlainCredentials(config.RABBIT_USER, config.RABBIT_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config.RABBIT_HOST, port=config.RABBIT_PORT, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue='vision_tasks', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='vision_tasks', on_message_callback=callback)

    print(" [*] Consumer uruchomiony. Czekam na zadania...")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()
