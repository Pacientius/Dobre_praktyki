from fastapi import FastAPI, HTTPException
import httpx
import config 
import subprocess
from pydantic import BaseModel
import sys
import os
import shutil
import anyio
import ocr_consumer

app = FastAPI(title="Main_Api")

class SaveADetails(BaseModel):
    uid: str = "TEST_UID_123"
    url: str = "https://elements-resized.envatousercontent.com/envato-dam-assets-production/EVA/TRX/01/1f/e6/44/b1/v1_E10/E102BHYV.jpg?w=500&cf_fit=scale-down&mark-alpha=18&mark=https%3A%2F%2Felements-assets.envato.com%2Fstatic%2Fwatermark4.png&q=85&format=auto&s=315bef5dfe9efe9bc22b1aeab148440c3b845f358d307881392adb7582596130"
    count: int = 1

class QueueBDetails(BaseModel):
    url: str = "https://elements-resized.envatousercontent.com/envato-dam-assets-production/EVA/TRX/01/1f/e6/44/b1/v1_E10/E102BHYV.jpg?w=500&cf_fit=scale-down&mark-alpha=18&mark=https%3A%2F%2Felements-assets.envato.com%2Fstatic%2Fwatermark4.png&q=85&format=auto&s=315bef5dfe9efe9bc22b1aeab148440c3b845f358d307881392adb7582596130"

class QueueOCRDetails(BaseModel):
    url: str = "https://upload.wikimedia.org/wikipedia/commons/1/11/Tablica_rejestracyjna_waskie_znaki.jpg"


class OCRDirectRequest(BaseModel):
    url: str = "https://upload.wikimedia.org/wikipedia/commons/1/11/Tablica_rejestracyjna_waskie_znaki.jpg"

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


@app.post("/queue_OCR")
async def queue_ocr(payload: QueueOCRDetails):
    try:
        async with httpx.AsyncClient() as client:
            target = f"http://{config.SERVICE_B_HOST}:{config.SERVICE_B_PORT}/queue_ocr"
            resp = await client.post(target, json=payload.dict(), timeout=5.0)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd komunikacji z Serwisem B (OCR): {str(e)}")


@app.post("/ocr_direct",)
async def ocr_direct(payload: OCRDirectRequest):
    try:
        plate = await anyio.to_thread.run_sync(
            ocr_consumer.process_image_url,
            payload.url,
            None,
            False,
        )

        if not plate:
            raise HTTPException(status_code=422, detail="Nie udało się odczytać tablicy z obrazu")

        return {"status": "success", "plate_number": plate, "source_url": payload.url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd OCR: {str(e)}")


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


@app.get("/status_OCR/{task_id}")
async def status_ocr(task_id: str):
    try:
        async with httpx.AsyncClient() as client:
            target = f"http://{config.SERVICE_B_HOST}:{config.SERVICE_B_PORT}/status/{task_id}"
            resp = await client.get(target, timeout=5.0)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd statusu OCR w Serwisie B: {str(e)}")


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


'''@app.post("/cleanup_tmp", name="Czyszczenie katalogu .tmp")
async def cleanup_tmp():
    """Clean up downloaded images and debug files from .tmp directory"""
    try:
        tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tmp')
        
        if not os.path.exists(tmp_dir):
            return {"status": "info", "message": "Directory .tmp does not exist"}
        
        files_removed = 0
        total_size = 0
        
        # Remove OCR images and crops
        for filename in os.listdir(tmp_dir):
            file_path = os.path.join(tmp_dir, filename)
            
            # Skip log files and debug directories
            if filename.endswith('.txt') or os.path.isdir(file_path):
                continue
            
            # Remove image files
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                files_removed += 1
                total_size += file_size
        
        return {
            "status": "success",
            "files_removed": files_removed,
            "space_freed_mb": round(total_size / (1024 * 1024), 2),
            "message": f"Cleaned up {files_removed} files, freed {round(total_size / (1024 * 1024), 2)} MB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")'''


'''@app.get("/tmp_status", name="Status katalogu .tmp")
async def tmp_status():
    """Get information about .tmp directory contents"""
    try:
        tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tmp')
        
        if not os.path.exists(tmp_dir):
            return {"status": "info", "message": "Directory .tmp does not exist"}
        
        total_files = 0
        total_size = 0
        file_types = {}
        
        for filename in os.listdir(tmp_dir):
            file_path = os.path.join(tmp_dir, filename)
            
            if os.path.isfile(file_path):
                total_files += 1
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Count by extension
                ext = os.path.splitext(filename)[1] or 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            "status": "success",
            "directory": tmp_dir,
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")'''

