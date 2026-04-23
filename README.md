# Badminton Video Editor - Full Stack Application

An AI-powered web application that automatically detects badminton rally segments and removes dead-time ball-picking scenes between points. Built with FastAPI backend and React frontend.

## 🎯 Features

- **Video Upload**: Drag-and-drop interface for video uploads
- **Shuttlecock Detection**: AI-based detection using YOLOv8 (mock implementation for demo)
- **Smart Smoothing**: Sliding window algorithm to reduce false positives
- **Automatic Cutting**: Extracts continuous rally segments
- **Video Stitching**: Combines valid segments into a single edited video
- **Real-time Progress**: Live status updates during processing
- **Easy Download**: One-click download of edited video

## 📋 Project Structure

```
Badminton Editor/
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── UploadForm.jsx
│   │   │   ├── UploadForm.css
│   │   │   ├── ProcessingStatus.jsx
│   │   │   ├── ProcessingStatus.css
│   │   │   ├── ResultsView.jsx
│   │   │   ├── ResultsView.css
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   ├── index.css
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .gitignore
├── backend/                  # FastAPI backend
│   ├── models/
│   │   ├── __init__.py
│   │   └── shuttlecock_detector.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── video_processor.py
│   ├── uploads/              # Video upload directory
│   ├── app.py               # Main FastAPI application
│   ├── requirements.txt
│   ├── .env
│   └── .gitignore
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v16+) and npm
- **Python** (3.8+)
- **FFmpeg** (for video processing)

### Installation & Setup

#### 1. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python app.py
```

The backend will start at `http://localhost:8000`

**API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs

#### 3. Frontend Setup

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will start at `http://localhost:3000`

### 🎮 Using the Application

1. Open browser to `http://localhost:3000`
2. **Upload**: Drag and drop a badminton video or click to select
3. **Processing**: The app will:
   - Detect shuttlecock in each frame
   - Apply smoothing to reduce noise
   - Extract valid rally segments
   - Cut and stitch the video
4. **Download**: Click "Download Edited Video" to get your processed video
5. **Review**: Check the detected intervals in the results view

### 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/config` | Get API configuration |
| POST | `/api/upload` | Upload video file |
| POST | `/api/process` | Start processing job |
| GET | `/api/status/{job_id}` | Check processing status |
| GET | `/api/download/{video_id}` | Download processed video |
| DELETE | `/api/cleanup/{video_id}` | Delete video files |

### ⚙️ Configuration

**Backend** (`.env`):
```
UPLOAD_DIR=./uploads
TEMP_DIR=./temp_segments
MAX_VIDEO_SIZE=500000000
```

**Video Processing Parameters** (`app.py` - `/api/process`):
- `window_size`: Sliding window size (default: 20 frames)
- `threshold`: Minimum detections to mark as valid (default: 10)

Adjust these parameters based on:
- Video FPS rate
- Rally duration
- Desired sensitivity

### 🤖 Model Integration

Currently, the detection uses a **mock implementation** for demo purposes.

To integrate **real YOLOv8 detection**:

1. **Install YOLOv8:**
   ```bash
   pip install ultralytics
   ```

2. **Update `backend/models/shuttlecock_detector.py`:**
   ```python
   from ultralytics import YOLO
   
   def __init__(self, model_path: str = None):
       self.model = YOLO(model_path or "yolov8n.pt")
   
   def detect_frame(self, frame: np.ndarray) -> dict:
       results = self.model(frame)
       detected = len(results[0].boxes) > 0
       # ... extract bbox and confidence ...
   ```

3. **Train your model** with your badminton dataset

### 📊 Processing Pipeline

```
Input Video
    ↓
Frame-by-frame Detection (YOLO)
    ↓
Assign Labels (has_ball: 0/1)
    ↓
Sliding Window Smoothing
    ↓
Extract Continuous Intervals
    ↓
Cut Video Segments
    ↓
Concatenate Segments
    ↓
Output Video (Rally Highlight)
```

### 🎬 Example Workflow

1. **Input**: 5-minute badminton video (300 seconds @ 30fps = 9000 frames)
2. **Detection**: 60% have shuttlecock detected (random in demo, actual in real model)
3. **Smoothing**: Using 20-frame window, 10-frame threshold
4. **Result**: ~40-60 seconds of edited highlights (continuous rallies)

### 💾 File Management

- **Uploaded videos**: `backend/uploads/{video_id}.mp4`
- **Processed videos**: `backend/uploads/{video_id}_processed.mp4`
- **Temporary segments**: `backend/temp_segments/segment_*.mp4`

**Cleanup**: Use the "Clean Up Files" button in the frontend, or:
```bash
curl -X DELETE http://localhost:8000/api/cleanup/{video_id}
```

### 🧪 Testing

**Test curl requests:**

```bash
# Upload video
curl -X POST -F "file=@/path/to/video.mp4" http://localhost:8000/api/upload

# Start processing
curl -X POST "http://localhost:8000/api/process?video_id=YOUR_VIDEO_ID"

# Check status
curl http://localhost:8000/api/status/YOUR_JOB_ID

# Download result
curl http://localhost:8000/api/download/YOUR_VIDEO_ID --output result.mp4
```

### 🐛 Troubleshooting

**Issue: "Cannot connect to backend"**
- Ensure backend is running: `python backend/app.py`
- Check port 8000 is not in use: `lsof -i :8000`

**Issue: "Video processing fails"**
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check video format is supported: `.mp4`, `.avi`, `.mov`, `.mkv`
- Check file size doesn't exceed limit (500MB default)

**Issue: "CORS errors"**
- Backend CORS is configured for all origins in demo mode
- In production, update to specific frontend URL

**Issue: "Out of disk space"**
- Clean up `backend/uploads/` and `backend/temp_segments/`
- Adjust `MAX_VIDEO_SIZE` if needed

### 🚢 Production Deployment

1. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Use production ASGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 backend.app:app
   ```

3. **Set up environment variables** for database, storage, etc.

4. **Configure CORS** for your domain

5. **Use HTTPS** and proper security headers

### 📚 Future Enhancements

- [ ] Real YOLOv8 model trained on custom badminton dataset
- [ ] Video preview before/after
- [ ] Batch processing
- [ ] WebSocket for real-time progress
- [ ] Database for job history
- [ ] Multi-user authentication
- [ ] S3 cloud storage integration
- [ ] Automated model retraining pipeline
- [ ] Support for other sports

### 📄 License

MIT License - Free to use and modify

### 👥 Authors

Created for AI-powered sports video editing

---

**Happy editing! 🏸**
