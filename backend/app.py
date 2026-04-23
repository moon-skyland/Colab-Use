"""
FastAPI backend for badminton video editor.

This application provides endpoints for:
1. Video upload
2. Shuttlecock detection and processing
3. Processed video download
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from models.shuttlecock_detector import ShuttlecockDetector
from utils.video_processor import process_video_pipeline

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Badminton Video Editor API",
    description="AI-powered video editor for badminton",
    version="1.0.0"
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
TEMP_DIR = os.getenv("TEMP_DIR", "./temp_segments")
MAX_VIDEO_SIZE = int(os.getenv("MAX_VIDEO_SIZE", 500000000))  # 500MB default

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize detector
detector = ShuttlecockDetector()

# Store job status
job_status = {}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Badminton Video Editor API"}


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a badminton video for processing.
    
    Returns:
        - video_id: Unique identifier for the uploaded video
        - filename: Original filename
        - message: Success message
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(
                status_code=400,
                detail="Only video files are allowed (.mp4, .avi, .mov, .mkv)"
            )
        
        # Generate unique video ID
        import uuid
        video_id = str(uuid.uuid4())
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_VIDEO_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_VIDEO_SIZE / 1e6:.0f}MB"
            )
        
        return {
            "video_id": video_id,
            "filename": file.filename,
            "file_size": file_size,
            "message": "Video uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process")
async def process_video(
    video_id: str,
    window_size: int = 20,
    threshold: int = 10,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Process uploaded video: detect shuttlecock, smooth, extract rallies, and cut.
    
    Args:
        video_id: ID returned from upload endpoint
        window_size: Sliding window size for smoothing
        threshold: Minimum detections in window to mark as valid
        
    Returns:
        - job_id: Identifier for tracking progress
        - status: Current processing status
    """
    try:
        # Validate video exists
        input_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        job_status[job_id] = {
            "status": "processing",
            "video_id": video_id,
            "progress": 0,
            "error": None
        }
        
        # Run processing asynchronously
        background_tasks.add_task(
            _process_video_task,
            job_id,
            input_path,
            video_id,
            window_size,
            threshold
        )
        
        return {
            "job_id": job_id,
            "video_id": video_id,
            "status": "queued",
            "message": "Processing started"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _process_video_task(job_id: str, input_path: str, video_id: str, window_size: int, threshold: int):
    """Background task for video processing."""
    try:
        output_path = os.path.join(UPLOAD_DIR, f"{video_id}_processed.mp4")
        
        # Step 1: Run detection
        job_status[job_id]["status"] = "detecting"
        detections = detector.process_video(input_path)
        
        # Step 2: Process video (smooth, extract, cut, stitch)
        job_status[job_id]["status"] = "processing"
        result = process_video_pipeline(
            input_path,
            output_path,
            detections,
            window_size,
            threshold,
            TEMP_DIR
        )
        
        if result["success"]:
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["result"] = result
            job_status[job_id]["progress"] = 100
        else:
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["error"] = result.get("error", "Unknown error")
    
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["error"] = str(e)


@app.get("/api/status/{job_id}")
def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job_status[job_id]
    return {
        "job_id": job_id,
        "status": status["status"],
        "progress": status.get("progress", 0),
        "error": status.get("error"),
        "result": status.get("result")
    }


@app.get("/api/download/{video_id}")
def download_processed_video(video_id: str):
    """Download the processed/edited video."""
    try:
        file_path = os.path.join(UPLOAD_DIR, f"{video_id}_processed.mp4")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Processed video not found")
        
        return FileResponse(
            path=file_path,
            filename=f"badminton_edited_{video_id}.mp4",
            media_type="video/mp4"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/cleanup/{video_id}")
def cleanup_video(video_id: str):
    """Delete uploaded and processed video files."""
    try:
        # Delete original
        original_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
        if os.path.exists(original_path):
            os.remove(original_path)
        
        # Delete processed
        processed_path = os.path.join(UPLOAD_DIR, f"{video_id}_processed.mp4")
        if os.path.exists(processed_path):
            os.remove(processed_path)
        
        return {"message": "Files cleaned up successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
def get_config():
    """Get API configuration (for frontend)."""
    return {
        "max_file_size_mb": MAX_VIDEO_SIZE / 1e6,
        "supported_formats": ["mp4", "avi", "mov", "mkv"],
        "api_url": "http://localhost:8000"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
