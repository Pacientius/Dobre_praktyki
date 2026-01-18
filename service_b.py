from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import json
import config
import uuid
import time

app = FastAPI(title="Service B - zapis na kolejke")

r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

class AnalyzeRequest(BaseModel):
    url: str

@app.post("/queue", status_code=201)
async def enqueue_task(payload: AnalyzeRequest):
    try:
        task_id = str(uuid.uuid4())

        job_data = {
            "id": task_id,
            "status": "queued",
            "url": payload.url,
            "created_at": time.asctime()
        }

        r.set(task_id, json.dumps(job_data), ex=3600) #3600 godzina na wygaśniecie
        r.lpush("AI_queue", task_id)

        return {"status": "success", "data": job_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd kolejkowania: {str(e)}")


@app.post("/queue_ocr", status_code=201)
async def enqueue_ocr_task(payload: AnalyzeRequest):
    try:
        task_id = str(uuid.uuid4())

        job_data = {
            "id": task_id,
            "status": "queued",
            "url": payload.url,
            "created_at": time.asctime()
        }

        r.set(task_id, json.dumps(job_data), ex=3600)
        r.lpush("OCR_queue", task_id)

        return {"status": "success", "data": job_data, "queue": "OCR_queue"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd kolejkowania OCR: {str(e)}")

    
@app.get("/status/{task_id}")
async def get_status(task_id: str):
    data = r.get(task_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Task done or expired")
    
    return json.loads(data)


@app.get("/health", status_code=200)
async def health_check():
    try:
        status = r.connection
        ping = r.ping()
        return {"status": "ok", "connection": status, "ping": ping}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"status: error , reason: {str(e)}")        

