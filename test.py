import pytest
import httpx
import uuid
import mysql.connector
import config

BASE_URL = f"http://{config.LOCAL_IP if config.LOCAL_TEST else 'localhost'}:8000"

@pytest.fixture
def db_connection():
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME
    )
    yield conn
    conn.close()

@pytest.fixture
def api_client():
    with httpx.Client(timeout=30.0) as client:
        yield client

def test_full_system_flow(api_client, db_connection):
    test_url = f"images.com_{uuid.uuid4().hex[:6]}.png"
    expected_count = 5

    res_q = api_client.post(f"{BASE_URL}/queue_B", json={"url": test_url})
    assert res_q.status_code == 200
    task_id = res_q.json()["data"]["id"]

    res_save = api_client.post(f"{BASE_URL}/save_A", json={
        "uid": task_id,
        "url": test_url,
        "count": expected_count
    })
    assert res_save.status_code == 200

    cursor = db_connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM detections WHERE uid = %s", (task_id,))
    record = cursor.fetchone()
    cursor.close()

    assert record is not None, f"Nie znaleziono rekordu {task_id} w bazie!"
    assert record['people_count'] == expected_count
    assert record['image_url'] == test_url

def test_health_endpoints(api_client):

    assert api_client.post(f"{BASE_URL}/health-check-a").status_code == 200
    assert api_client.post(f"{BASE_URL}/health-check-b").status_code == 200
