from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import os
import sys
import uuid
import time
from analyze_results_v2 import analyze_image

# Add current directory to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

# Enable CORS for Next.js frontend (which usually runs on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory job store (Use a database/Redis for production)
jobs = {}

def process_analysis(job_id: str, file_path: str, age: str, gender: str):
    """Background task wrapper"""
    try:
        jobs[job_id]["status"] = "processing"
        print(f"[JOB {job_id[:8]}] Starting analysis...")
        
        base_name = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        report_path = os.path.join(os.path.dirname(file_path), f"{file_name_without_ext}_analysis.txt")
        
        result_text = analyze_image(file_path, age=age, gender=gender)
        
        # Check if the result is an error message from the model
        if result_text and result_text.startswith("Error"):
            print(f"[JOB {job_id[:8]}] Failed: {result_text}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = result_text
        else:
            print(f"[JOB {job_id[:8]}] Completed successfully ({len(result_text)} chars)")
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {
                "analysis": result_text,
                "report_path": report_path if os.path.exists(report_path) else None
            }
    except Exception as e:
        print(f"[JOB {job_id[:8]}] Exception: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.get("/")
def read_root():
    return {"status": "online", "message": "TahalilAI Backend is running"}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return {"status": "not_found"}
    return job

@app.post("/analyze")
def analyze_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    age: str = Form(None),
    gender: str = Form(None),
    wait_for_result: bool = Form(False)
):
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"Received file: {file_path}, Age: {age}, Gender: {gender}")
        
        # Create a job ID
        job_id = str(uuid.uuid4())
        
        if wait_for_result:
            # SYNCHRONOUS MODE (for Swagger testing)
            # Run directly and return the result in the same HTTP response
            jobs[job_id] = {"status": "processing", "submitted_at": time.time()}
            process_analysis(job_id, file_path, age, gender)
            
            job_data = jobs[job_id]
            elapsed = round(time.time() - job_data.get("submitted_at", 0), 1)
            
            if job_data["status"] == "completed":
                return JSONResponse(content={
                    "status": "completed",
                    "job_id": job_id,
                    "elapsed_seconds": elapsed,
                    "result": job_data["result"]
                })
            else:
                return JSONResponse(content={
                    "status": job_data["status"],
                    "job_id": job_id,
                    "elapsed_seconds": elapsed,
                    "error": job_data.get("error", "Unknown error")
                }, status_code=500)
        else:
            # ASYNC MODE (for frontend polling)
            jobs[job_id] = {"status": "queued", "submitted_at": time.time()}
            background_tasks.add_task(process_analysis, job_id, file_path, age, gender)
            
            return JSONResponse(content={
                "status": "queued",
                "job_id": job_id,
                "message": "Processing started. Poll /status/<job_id> for results."
            })
        
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    # Verify paths before starting
    print(f"Server starting. Upload dir: {UPLOAD_DIR}")
    # Run with extended timeout settings to support slow CPU inference
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=700)
