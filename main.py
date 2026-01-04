from fastapi import FastAPI, HTTPException
import httpx
import config 
import subprocess
from pydantic import BaseModel
import sys

app = FastAPI(title="Main_Api")

class SaveADetails(BaseModel):
    uid: str = "default_uuid_123"
    url: str = "https://elements-resized.envatousercontent.com/envato-dam-assets-production/EVA/TRX/01/1f/e6/44/b1/v1_E10/E102BHYV.jpg?w=500&cf_fit=scale-down&mark-alpha=18&mark=https%3A%2F%2Felements-assets.envato.com%2Fstatic%2Fwatermark4.png&q=85&format=auto&s=315bef5dfe9efe9bc22b1aeab148440c3b845f358d307881392adb7582596130"
    count: int = 1

class QueueBDetails(BaseModel):
    url: str = "https://elements-resized.envatousercontent.com/envato-dam-assets-production/EVA/TRX/01/1f/e6/44/b1/v1_E10/E102BHYV.jpg?w=500&cf_fit=scale-down&mark-alpha=18&mark=https%3A%2F%2Felements-assets.envato.com%2Fstatic%2Fwatermark4.png&q=85&format=auto&s=315bef5dfe9efe9bc22b1aeab148440c3b845f358d307881392adb7582596130"

@app.post("/save_A")
async def service_A(payload: SaveADetails):
    try:
        async with httpx.AsyncClient() as client:
            target = f"http://{config.SERVICE_A_HOST}:{config.SERVICE_A_PORT}/save"
            resp = await client.post(target, json=payload.dict(), timeout=5.0)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd komunikacji z Serwisem A: {str(e)}")

@app.post("/queue_B")
async def service_B(payload: QueueBDetails):
    try:
        async with httpx.AsyncClient() as client:
            target = f"http://{config.SERVICE_B_HOST}:{config.SERVICE_B_PORT}/queue"
            resp = await client.post(target, json=payload.dict(), timeout=5.0)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd komunikacji z Serwisem B: {str(e)}")


@app.get("/status_B/{task_id}")
async def status_B(task_id: str):
    try:
        async with httpx.AsyncClient() as client:
            target = f"http://{config.SERVICE_B_HOST}:{config.SERVICE_B_PORT}/status/{task_id}"
            resp = await client.get(target, timeout=5.0)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd statusu w Serwisie B: {str(e)}")


@app.get("/run-tests")
async def run_tests():
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "test.py", "--tb=short", "-s"], 
            capture_output=True, 
            text=True
        )
        return {
            "status": "success" if res.returncode == 0 else "failed",
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"error": str(e)}
    

@app.post("/health-check-a",name="Health Check dodawanie do bzy")
async def health_check_a():
    try:
        async with httpx.AsyncClient() as client:
            target = f"http://{config.SERVICE_A_HOST}:{config.SERVICE_A_PORT}/health"
            resp = await client.get(target, timeout=5.0)
            resp.raise_for_status()
            return {"status": "healthy", "service_a_status": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service A unhealthy")
    

@app.post("/health-check-b", name="Health Check zapis na kolejke ")
async def health_check_b():
    try:
        async with httpx.AsyncClient() as client:
            target = f"http://{config.SERVICE_B_HOST}:{config.SERVICE_B_PORT}/health"
            resp = await client.get(target, timeout=5.0)
            resp.raise_for_status()
            return {"status": "healthy", "service_b_status": resp.json()}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service B unhealthy")

