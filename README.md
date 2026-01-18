testy:
docker compose up -d db redis phpmyadmin redis-commander redis-insight


.\.venv\Scripts\Activate.ps1


uvicorn main:app --port 8000 --reload
uvicorn service_a:app --port 8101 --reload
uvicorn service_b:app --port 8102 --reload

python .\consumer.py

python .\ocr_consumer.py  
python .\ocr_consumer.py --test




dobre_praktyki_programowania> python .\ocr_consumer.py --test:
============================================================
TEST RESULTS
============================================================
Total images:  195
Correct:       185
Accuracy:      94.87%
Total time:    12.76 sec
Speed:         6.54 sec / 100 images 
Grade:         5.0
============================================================

speed zmienia ocene a zelezy glownie od sprzetu