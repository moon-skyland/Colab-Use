# 🏸 Badminton Video Editor

An intelligent machine learning-powered video editor that automatically detects and segments badminton gameplay points from full match videos. The system recognizes when points are being played versus when players are picking up shuttles during breaks.

## Features

✨ **Key Capabilities**:
- **ML-Based Point Detection**: Automatically identifies when badminton points are active vs. break periods
- **Motion Analysis**: Uses optical flow and motion scoring to detect gameplay activity
- **Intelligent Segmentation**: Divides videos into labeled segments (point/break)
- **Custom Editing**: Remove break periods or keep only active gameplay
- **Web Interface**: Modern, responsive UI for easy video management
- **Background Processing**: Non-blocking video processing with progress tracking
- **Database Storage**: SQLite for video and segment metadata

## Project Structure

```
Badminton Editor/
├── backend.py          # Flask backend + ML engine + Database
├── frontend.html       # Web interface (single file, no build needed)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- macOS, Linux, or Windows

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start the Backend

```bash
python backend.py
```

You should see:
```
WARNING in app.run_with_reloader
 * Running on http://localhost:5000
```

### Step 3: Open the Frontend

Simply open the `frontend.html` file in your web browser:
```bash
open frontend.html   # macOS
# or
start frontend.html  # Windows
# or use your browser to open the file
```

Or navigate to the file directly in your browser.

## How It Works

### Architecture Overview

```
┌─────────────────────┐
│   Frontend (HTML)   │  Web interface for upload & control
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────────────────────────┐
│         Backend (Flask/Python)          │
├─────────────────────────────────────────┤
│ 1. File Upload Handler                  │
│ 2. ML Point Detector (Motion Analysis)  │
│ 3. Video Processing Engine              │
│ 4. SQLite Database (Videos & Segments)  │
│ 5. Video Editing/Export                 │
└─────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────┐
    │   Video Files       │
    │   SQLite DB         │
    │   Edited Output     │
    └─────────────────────┘
```

### Machine Learning Pipeline

The ML model works through these steps:

1. **Video Frame Extraction**: Load video at native FPS
2. **Frame Buffering**: Maintain sliding window of frames (30-frame buffer)
3. **Motion Detection**: Calculate optical flow between consecutive frames
4. **Motion Scoring**: Sum absolute differences in grayscale frames
5. **Threshold Analysis**: 
   - If avg_motion > 5000: **Point Active** (high motion = gameplay)
   - If avg_motion < 2000: **Break Period** (low motion = pickup time)
6. **State Transitions**: Detect changes from point→break or break→point
7. **Segment Creation**: Generate start/end times and labels

### Video Editing Process

When you click "Create Edited Video":
- Select which segments to keep (Points, Breaks, or both)
- The system re-encodes the video keeping only selected segments
- Edited video is saved with timestamp: `edited_{video_id}_{timestamp}.mp4`

## API Endpoints

### Health Check
```
GET /api/health
```
Response: `{"status": "ok", "message": "Badminton Editor Backend Running"}`

### Upload Video
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (video file)
```
Response: Video ID, filename, duration, FPS, processing status

### List Videos
```
GET /api/videos
```
Response: Array of all uploaded videos with metadata

### Get Video Segments
```
GET /api/video/{video_id}/segments
```
Response: Array of detected segments with timestamps and labels

### Get Processing Status
```
GET /api/video/{video_id}/status
```
Response: Current status and progress percentage

### Edit Video
```
POST /api/video/{video_id}/edit
Content-Type: application/json
Body: {"keep_labels": ["point"]}
```
Response: Output filename and path

## Database Schema

### Videos Table
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    original_path TEXT,
    upload_date TIMESTAMP,
    duration REAL,
    fps REAL,
    status TEXT
);
```

### Segments Table
```sql
CREATE TABLE segments (
    id INTEGER PRIMARY KEY,
    video_id INTEGER,
    start_frame INTEGER,
    end_frame INTEGER,
    start_time REAL,
    end_time REAL,
    label TEXT,           -- 'point' or 'break'
    duration REAL,
    FOREIGN KEY(video_id) REFERENCES videos(id)
);
```

### Edited Videos Table
```sql
CREATE TABLE edited_videos (
    id INTEGER PRIMARY KEY,
    video_id INTEGER,
    output_path TEXT,
    edit_type TEXT,
    segments_included TEXT,
    created_date TIMESTAMP,
    FOREIGN KEY(video_id) REFERENCES videos(id)
);
```

## Configuration

Edit these parameters in `backend.py` to tune the ML model:

```python
class BadmintonPointDetector:
    def __init__(self):
        self.motion_threshold = 5000      # Increase = stricter point detection
        self.still_threshold = 2000       # Increase = longer break periods
        self.buffer_size = 30             # Frame buffer for analysis
```

## Performance Tips

1. **Video Optimization**: Pre-encode videos to 720p for faster processing
2. **Batch Processing**: Process multiple videos sequentially or in parallel
3. **Memory**: For large videos (>2GB), consider breaking into segments
4. **GPU Acceleration**: For significant speedup, install `opencv-python-headless` with CUDA support

## Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Videos Not Processing
1. Check backend console for errors
2. Verify video codec is supported (H.264, VP9, etc.)
3. Check available disk space for uploads and edited output

### Poor Point Detection
1. Adjust `motion_threshold` in `backend.py`
2. Test with well-lit videos first
3. Ensure video has clear camera movement detection

### CORS Errors
Already handled with Flask-CORS configuration in backend.

## Extending the System

### Improve ML Model
Replace `detect_motion()` with more sophisticated methods:
- TensorFlow/PyTorch models for player tracking
- YOLO for badminton detection
- Activity recognition models

### Add Features
- Video preview in browser
- Frame-by-frame scrubbing
- Manual segment adjustment UI
- Batch export options
- Support for live video streams

### Scale Up
- Replace Flask with FastAPI for async processing
- Use Celery + Redis for task queue
- Deploy with Docker + Kubernetes
- Use object storage (S3) instead of local files

## File Organization

```
uploads/                    # Uploaded videos
edited_videos/              # Edited video outputs
badminton_videos.db        # SQLite database
```

## License & Notes

This is a foundation project for badminton video analysis. The ML model is a basic motion detector suitable for prototyping. For production use, consider implementing more sophisticated computer vision techniques.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend console output
3. Verify all dependencies are installed
4. Ensure ports 5000 (backend) is available

---

Built with ❤️ for badminton enthusiasts
