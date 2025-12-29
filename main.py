from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from producer import publish_task

app = FastAPI()

class ImageRequest(BaseModel):
    url: str

@app.post("/analyze_img")
async def analyze_img(request: ImageRequest):
    if not request.url:
        raise HTTPException(status_code=400, detail="URL nie może być pusty")
    
    try:
        publish_task(request.url)
        return {"status": "Zlecono", "msg": "Zadanie dodane do kolejki", "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd RabbitMQ: {str(e)}")


@app.get("/analyze_img")
async def analyze_img_get(url: str):
    publish_task(url)
    return {"status": "Zlecono", "url": url}
