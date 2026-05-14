"""FastAPI API for upload/process/status/preview/download flow."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from backend.pipeline import process_video_pipeline
except ImportError:
    try:
        from .pipeline import process_video_pipeline  # type: ignore
    except Exception:
        from pipeline import process_video_pipeline


app = FastAPI(title="Badminton AI Editor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = Path("backend/uploads")
OUTPUTS_DIR = Path("backend/outputs")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

jobs: dict[str, dict] = {}

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Badminton AI Editor backend is running"}


@app.post("/upload")
async def upload_video(video: UploadFile = File(...)) -> dict[str, str]:
    if not video.filename:
        raise HTTPException(status_code=400, detail="Missing uploaded filename.")

    job_id = str(uuid.uuid4())
    safe_name = Path(video.filename).name
    saved_path = UPLOADS_DIR / f"{job_id}_{safe_name}"

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}") from exc

    jobs[job_id] = {
        "job_id": job_id,
        "uploaded_video_path": str(saved_path),
        "status": "uploaded",
        "outputs": {},
        "error": None,
    }
    return {
        "job_id": job_id,
        "video_path": str(saved_path),
        "message": "Upload successful",
    }


@app.post("/process/{job_id}")
def process_job(job_id: str) -> dict[str, str]:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    uploaded_path = Path(job["uploaded_video_path"])
    if not uploaded_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded video not found for job.")

    output_dir = OUTPUTS_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    job["status"] = "processing"
    job["error"] = None

    result = process_video_pipeline(
        video_path=str(uploaded_path),
        court_corners_json=None,
        output_dir=str(output_dir),
        max_frames=0,
        window_size_seconds=1.0,
        use_mock_if_missing=True,
    )

    if result.get("status") != "success":
        job["status"] = "failed"
        job["error"] = str(result.get("error", "Unknown processing error"))
        return {
            "job_id": job_id,
            "status": "failed",
            "error": job["error"],
        }

    job["status"] = "success"
    job["outputs"] = result

    return {
        "job_id": job_id,
        "status": "success",
        "edited_video_url": f"/outputs/{job_id}/edited_video.mp4",
        "edit_instruction_url": f"/outputs/{job_id}/edit_instruction.json",
        "state_timeline_url": f"/outputs/{job_id}/state_timeline.json",
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
