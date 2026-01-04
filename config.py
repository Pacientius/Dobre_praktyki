import os
from dotenv import load_dotenv

load_dotenv()



LOCAL_TEST = os.getenv("LOCAL_TEST", "False") == "True"
LOCAL_IP = os.getenv("LOCAL_IP", "127.0.0.1")
SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")





if LOCAL_TEST:
    DB_HOST = SERVER_IP
else:
    DB_HOST = "db"

DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "password")
DB_NAME = os.getenv("DB_NAME", "detection")


if LOCAL_TEST:
    REDIS_HOST = SERVER_IP
else:
    REDIS_HOST = "redis"

REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USER = os.getenv("REDIS_USER", "guest")
REDIS_PASS = os.getenv("REDIS_PASS", "guest")


if LOCAL_TEST:
    SERVICE_A_HOST = LOCAL_IP
    SERVICE_B_HOST = LOCAL_IP
    SERVICE_A_PORT = int(os.getenv("SERVICE_A_PORT", 8101))
    SERVICE_B_PORT = int(os.getenv("SERVICE_B_PORT", 8102))
else:
    SERVICE_A_HOST = "service_a"
    SERVICE_B_HOST = "service_b"
    SERVICE_A_PORT = 8101
    SERVICE_B_PORT = 8102



print("================================")
print("TRYB:", "LOCAL (VS CODE)" if LOCAL_TEST else "FULL DOCKER")
print("DB HOST:", DB_HOST)
print("REDIS HOST:", REDIS_HOST)
print("================================")
