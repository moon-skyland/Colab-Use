# 🏸 Badminton Video Editor - Project Overview

## ✅ What We Built

A **full-stack, AI-powered badminton video editor** that:
- Accepts video uploads via web UI
- Detects shuttlecock frames using YOLO-based detection (mock in demo)
- Applies intelligent smoothing to filter out noise
- Automatically cuts and stitches valid rally segments
- Returns a cleaned, highlight-style video

**Stack:**
- **Frontend**: React + Vite (running on port 3000)
- **Backend**: FastAPI (running on port 8000)  
- **Video Processing**: OpenCV + FFmpeg
- **ML Model**: YOLOv8 (ready for integration)

---

## 📁 Project Structure (Complete)

```
Badminton Editor/
│
├── 📄 README.md                    # Full project documentation
├── 📄 QUICK_START.md               # 5-minute setup guide
├── 📄 PROJECT_OVERVIEW.md          # This file
│
├── frontend/                       # React web application
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadForm.jsx      # File upload UI with drag-drop
│   │   │   ├── UploadForm.css      # Upload styling
│   │   │   ├── ProcessingStatus.jsx # Real-time status display
│   │   │   ├── ProcessingStatus.css
│   │   │   ├── ResultsView.jsx     # Results and download
│   │   │   └── ResultsView.css
│   │   ├── App.jsx                 # Main app component
│   │   ├── App.css
│   │   ├── main.jsx                # React entry point
│   │   └── index.css               # Global styles
│   ├── public/                     # Static assets
│   ├── index.html                  # HTML template
│   ├── vite.config.js              # Vite configuration
│   ├── package.json                # Dependencies
│   └── .gitignore
│
└── backend/                        # FastAPI server
    ├── app.py                      # Main FastAPI application
    ├── requirements.txt            # Python dependencies
    ├── .env                        # Configuration
    ├── .gitignore
    │
    ├── models/
    │   ├── __init__.py
    │   └── shuttlecock_detector.py # Shuttle detection (YOLOv8)
    │
    ├── utils/
    │   ├── __init__.py
    │   └── video_processor.py      # Core video processing pipeline
    │
    ├── uploads/                    # Uploaded & processed videos
    │   (auto-created)
    │
    └── temp_segments/              # Temporary video clips
        (auto-created)
```

---

## 🔧 Backend Components

### 1. **app.py** - FastAPI Application
**Endpoints:**
- `GET /health` - Health check
- `GET /api/config` - Configuration info
- `POST /api/upload` - Upload video
- `POST /api/process` - Start processing
- `GET /api/status/{job_id}` - Check progress
- `GET /api/download/{video_id}` - Download result
- `DELETE /api/cleanup/{video_id}` - Delete files

**Features:**
- CORS enabled (localhost:3000)
- Background task processing
- Job status tracking
- File validation & size limits

### 2. **models/shuttlecock_detector.py**
**ShuttlecockDetector Class:**
- `detect_frame()` - Detect shuttle in single frame
- `process_video()` - Process entire video

**Current Implementation:**
- Mock detection (60% probability)
- Random bounding box generation
- **Ready to integrate real YOLOv8**

### 3. **utils/video_processor.py**
**Video Processing Pipeline:**
1. `smooth_detections()` - Sliding window filter
2. `extract_intervals()` - Find continuous segments
3. `get_video_properties()` - Analyze video
4. `extract_video_segment()` - Cut segment
5. `concatenate_videos()` - Stitch segments
6. `process_video_pipeline()` - Full pipeline orchestration

---

## 🎨 Frontend Components

### 1. **App.jsx** - Main Container
- Manages application state (upload → processing → results)
- Coordinates between components
- Handles API calls

### 2. **UploadForm.jsx** - Upload Interface
- Drag-and-drop support
- File validation
- Upload progress indicator
- Error handling

### 3. **ProcessingStatus.jsx** - Live Progress
- Polls backend for job status
- Displays percentage/status
- Shows detected intervals on completion
- Handles animations

### 4. **ResultsView.jsx** - Download & Results
- Shows processing summary
- Lists detected rally intervals
- Download button
- Process another button
- Cleanup functionality

---

## 🔄 Data Flow

```
┌─────────────┐
│   Browser   │ (localhost:3000)
└──────┬──────┘
       │
       ├─── File Upload ───┐
       │                   ↓
       │        ┌──────────────────┐
       │        │  UploadForm      │
       │        │  (validation)    │
       │        └────────┬─────────┘
       │                 │
       ├─────────────────┴────────────→ POST /api/upload
       │                                (Flask Backend)
       │                                ↓
       │                            ┌─────────────────┐
       │                            │  models/        │
       │                            │  detector.py    │
       │                            │  (detection)    │
       │                            └────────┬────────┘
       │                                     ↓
       │                            ┌─────────────────┐
       │                            │  utils/         │
       │                            │  video_proc.py  │
       │                            │  (smooth,cut)   │
       │                            └────────┬────────┘
       │                                     ↓
       ├──────── Poll Status ──→ GET /api/status/{job_id}
       │                        (check progress)
       │                                     ↓
       ├───────── Download ───→ GET /api/download/{video_id}
       │                        (receive edited video)
       │                                     ↓
       └─────────────────────────────────────┘
```

---

## ⚡ Key Features Implemented

### Frontend
✅ Modern, responsive UI  
✅ Drag-and-drop file upload  
✅ Real-time progress tracking  
✅ Error handling and validation  
✅ Video download functionality  
✅ Clean state management  

### Backend
✅ RESTful API design  
✅ Async background processing  
✅ Video I/O with OpenCV  
✅ Mock detection pipeline  
✅ Smoothing algorithm  
✅ Video cutting and stitching  
✅ Proper error handling  
✅ CORS configuration  

### Architecture
✅ Separation of concerns  
✅ Modular code structure  
✅ Easy to extend for real model  
✅ Clean configuration management  
✅ Production-ready patterns  

---

## 🚀 Getting Started

### Quick Start (5 minutes)
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Open http://localhost:3000
```

See **QUICK_START.md** for detailed instructions.

---

## 🎯 Processing Pipeline Explained

### Input: 5-minute badminton video

**Stage 1: Frame Detection**
- Read video frame-by-frame (30 fps × 300 sec = 9000 frames)
- For each frame: detect shuttlecock → has_ball = 0 or 1
- Demo: ~60% random positive detections

**Stage 2: Smoothing**
- Apply 20-frame sliding window
- If ≥10 frames in window have shuttlecock: mark window as "rally"
- Reduces noise from detection errors

**Stage 3: Interval Extraction**
- Find continuous periods where label = 1 (rally)
- Example result: [(100, 500), (620, 1200), ...] frames

**Stage 4: Video Cutting**
- Extract each frame range to temporary segment files
- Keep only the detected rally segments

**Stage 5: Stitching**
- Concatenate all segments in order
- Output single video with dead-time removed

**Output: 40-90 second highlight video**

---

## 🤖 Integrating Real YOLOv8

### Current State (Demo)
- Mock detection with 60% random positive rate
- Allows testing full pipeline without model

### Integration Steps
1. Install ultralytics: `pip install ultralytics`
2. Get/train YOLOv8 shuttlecock model
3. Update `ShuttlecockDetector.detect_frame()`:
   ```python
   from ultralytics import YOLO
   
   def detect_frame(self, frame):
       results = self.model(frame)
       if results[0].boxes:
           # Extract detection...
   ```
4. Use trained model path in initialization

### Training Your Own Model
```bash
# Label your dataset in YOLO format
# Then:
yolo detect train \
  data=badminton_data.yaml \
  model=yolov8n.pt \
  epochs=100 \
  imgsz=640
```

---

## 📊 Configuration

### Backend (`.env`)
```
UPLOAD_DIR=./uploads           # Where to save uploads
TEMP_DIR=./temp_segments       # Temporary clips
MAX_VIDEO_SIZE=500000000       # 500MB limit
```

### Processing Parameters (`app.py`)
```python
window_size: int = 20    # Frames per window
threshold: int = 10      # Min detections needed
```

### Frontend (Hardcoded)
```javascript
const API_URL = 'http://localhost:8000'
```

---

## 🧪 Testing

### Unit Test Mock Detection
```bash
cd backend
python -c "
from models.shuttlecock_detector import ShuttlecockDetector
import cv2
import numpy as np

detector = ShuttlecockDetector()
fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
result = detector.detect_frame(fake_frame)
print(result)
"
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Get config
curl http://localhost:8000/api/config

# Upload
curl -F "file=@test.mp4" http://localhost:8000/api/upload
```

---

## 📈 Performance Considerations

- **Video I/O**: OpenCV sequential frame reading (efficient)
- **Detection**: Mock is instant; real YOLOv8 ~20-50ms/frame
- **Smoothing**: O(n) linear pass
- **Stitching**: FFmpeg concat protocol (fast)

**Typical processing time:**
- 5-min video @ 30fps = 9000 frames
- Mock detection: ~1 second
- Real YOLOv8: ~3-7 minutes (GPU-accelerated)

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 3000/8000 in use | `lsof -i :3000` and kill process |
| CORS error | Backend CORS enabled, check frontend URL |
| FFmpeg not found | `brew install ffmpeg` (macOS) |
| No intervals detected | Adjust `threshold` parameter lower |
| Out of disk space | Run cleanup button or delete `uploads/` |

---

## ✨ What You Can Do Now

- ✅ Upload badminton videos via web UI
- ✅ See mock detection in action
- ✅ Download "edited" video with segments removed
- ✅ Understand full AI video editing pipeline
- ✅ Integrate real YOLOv8 model when ready
- ✅ Train on your own badminton dataset
- ✅ Deploy to production

---

## 🎓 Learning Resources

- **Frontend**: React hooks, Axios, Vite
- **Backend**: FastAPI, async programming, CORS
- **Video**: OpenCV, FFmpeg, frame-by-frame processing
- **ML**: YOLOv8, object detection, model deployment

---

## 📚 Next Steps

1. **Test with real videos** (longer than 30 seconds)
2. **Collect badminton dataset** for model training
3. **Annotate frames** with shuttlecock positions
4. **Train YOLOv8** on your dataset
5. **Replace mock detector** with trained model
6. **Fine-tune parameters** (window_size, threshold)
7. **Deploy** to cloud platform
8. **Add user authentication** for production

---

## 🎉 You're All Set!

Everything is ready to run. Pick up from **QUICK_START.md** to launch the app!

**Questions?** Check the README.md for detailed API docs and troubleshooting.

Happy badminton editing! 🏸
