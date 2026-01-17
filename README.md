testy:
docker compose up -d db redis phpmyadmin redis-commander redis-insight


.\.venv\Scripts\Activate.ps1



uvicorn service_a:app --port 8101 --reload
uvicorn service_b:app --port 8102 --reload

python .\consumer.py

python .\ocr_consumer.py --test