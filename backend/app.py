"""FastAPI backend for Part 5 upload/process/preview/download flow."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

try:
    from backend.model.common.video_utils import get_video_info
    from backend.pipeline import process_video_pipeline
except ImportError:
    from model.common.video_utils import get_video_info
    from pipeline import process_video_pipeline


app = FastAPI(
    title="Badminton Video Editor API",
    description="Part 5 end-to-end badminton video editing backend",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "backend/uploads"))
MAX_VIDEO_SIZE = int(os.getenv("MAX_VIDEO_SIZE", "500000000"))
COURT_CORNERS_JSON = os.getenv(
    "COURT_CORNERS_JSON",
    "backend/data/court_corners/sample_court_corners.json",
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

job_status: dict[str, dict] = {}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "Badminton Video Editor API"}


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)) -> dict[str, object]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")
    if not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(
            status_code=400,
            detail="Only video files are allowed (.mp4, .avi, .mov, .mkv).",
        )

    video_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{video_id}.mp4"
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {exc}") from exc

    file_size = file_path.stat().st_size
    if file_size > MAX_VIDEO_SIZE:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_VIDEO_SIZE / 1e6:.0f}MB",
        )

    return {
        "video_id": video_id,
        "filename": file.filename,
        "file_size": file_size,
        "message": "Video uploaded successfully",
    }


@app.post("/api/process")
async def process_video(
    video_id: str,
    max_frames: int = 0,
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict[str, object]:
    input_path = UPLOAD_DIR / f"{video_id}.mp4"
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    job_id = str(uuid.uuid4())
    job_status[job_id] = {
        "status": "queued",
        "video_id": video_id,
        "progress": 0,
        "error": None,
        "result": None,
    }
    background_tasks.add_task(
        _process_video_task,
        job_id,
        str(input_path),
        video_id,
        max_frames,
    )
    return {
        "job_id": job_id,
        "video_id": video_id,
        "status": "queued",
        "message": "Processing started",
    }


def _process_video_task(job_id: str, input_path: str, video_id: str, max_frames: int) -> None:
    try:
        output_path = str(UPLOAD_DIR / f"{video_id}_processed.mp4")
        video_info = get_video_info(input_path)
        job_status[job_id]["status"] = "processing"
        job_status[job_id]["progress"] = 20

        result = process_video_pipeline(
            video_path=input_path,
            court_corners_json=COURT_CORNERS_JSON,
            output_dir="backend/outputs",
            max_frames=max_frames,
            window_size_seconds=1.0,
            use_mock_if_missing=True,
        )
        # Ensure API download path is consistent with existing frontend endpoint.
        produced_video = Path(str(result.get("edited_video", output_path)))
        if produced_video.exists() and str(produced_video) != output_path:
            shutil.copy2(produced_video, output_path)
        job_status[job_id]["progress"] = 90

        instruction_json_path = Path(str(result["instruction_json"]))
        instruction_payload = json.loads(instruction_json_path.read_text(encoding="utf-8"))
        keep_intervals = instruction_payload.get("keep_intervals", [])

        job_status[job_id]["status"] = "completed"
        job_status[job_id]["progress"] = 100
        job_status[job_id]["result"] = {
            "success": True,
            "segment_count": len(keep_intervals),
            "original_frames": int(video_info.get("frame_count", 0)),
            "intervals": [
                [float(interval["start"]), float(interval["end"])]
                for interval in keep_intervals
            ],
            "edited_video_path": output_path,
            "artifacts": result,
        }
    except Exception as exc:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["error"] = str(exc)


@app.get("/api/status/{job_id}")
def get_job_status(job_id: str) -> dict[str, object]:
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    status = job_status[job_id]
    return {
        "job_id": job_id,
        "status": status["status"],
        "progress": status.get("progress", 0),
        "error": status.get("error"),
        "result": status.get("result"),
    }


@app.get("/api/download/{video_id}")
def download_processed_video(video_id: str) -> FileResponse:
    file_path = UPLOAD_DIR / f"{video_id}_processed.mp4"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Processed video not found")
    return FileResponse(
        path=str(file_path),
        filename=f"badminton_edited_{video_id}.mp4",
        media_type="video/mp4",
    )


@app.delete("/api/cleanup/{video_id}")
def cleanup_video(video_id: str) -> dict[str, str]:
    for candidate in [
        UPLOAD_DIR / f"{video_id}.mp4",
        UPLOAD_DIR / f"{video_id}_processed.mp4",
    ]:
        candidate.unlink(missing_ok=True)
    return {"message": "Files cleaned up successfully"}


@app.get("/api/config")
def get_config() -> dict[str, object]:
    return {
        "max_file_size_mb": MAX_VIDEO_SIZE / 1e6,
        "supported_formats": ["mp4", "avi", "mov", "mkv"],
        "api_url": "http://localhost:8000",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
