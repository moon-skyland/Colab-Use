# Badminton Video Editor - Quick Start Guide

This document provides step-by-step instructions to run the full-stack application locally.

## ⚡ 5-Minute Setup

### Step 1: Prerequisites Check

```bash
# Check Node.js (v16+)
node --version
npm --version

# Check Python (3.8+)
python3 --version

# Check FFmpeg
ffmpeg -version
```

If any are missing, install them:
- **macOS**: `brew install node python3 ffmpeg`
- **Ubuntu**: `sudo apt-get install nodejs npm python3 ffmpeg`

### Step 2: Start Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend (will listen on port 8000)
python app.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start Frontend (in another terminal)

```bash
cd frontend

# Install dependencies (one-time)
npm install

# Run development server (will listen on port 3000)
npm run dev
```

You should see:
```
VITE v5.0.0  ready in 500 ms

➜  Local:   http://localhost:3000/
```

### Step 4: Open in Browser

- Navigate to: **http://localhost:3000**
- You should see the Badminton Video Editor UI

## 🎮 First Run

1. **Prepare a test video**:
   - Get any MP4 video file (even a short one for testing)
   - Can be sports video, gameplay, or any clip

2. **Upload**:
   - Drag and drop into the upload area, or click to select
   - Wait for upload to complete

3. **Processing**:
   - Frontend automatically starts processing
   - You'll see status: "Detecting shuttlecock frames..."
   - Then: "Processing and cutting video..."
   - This uses mock detection (random for demo)

4. **Results**:
   - See detected rally segments
   - Click "Download Edited Video" to save the result
   - Click "Process Another Video" to start over

## 📊 What's Happening Under the Hood

**Frame Detection Pipeline:**
```
1. Read video frame-by-frame
2. Mock detection: ~60% probability shuttlecock exists (random in demo)
3. Assign labels: has_ball = 0 or 1
4. Smooth with sliding window (20 frames, 10-frame threshold)
5. Extract continuous segments where has_ball = 1
6. Cut video at segment boundaries
7. Stitch segments together
8. Output edited video
```

## 🔍 Monitor Progress

**Check backend logs in terminal:**
```
Processing video XYZ
Frame 1/300, Detecting...
Frame 50/300, Detecting...
...
Smoothing results
Extracting intervals
Found 5 rally segments
Stitching video...
Complete!
```

**Check frontend:**
- Progress bar shows percentage (0-100%)
- Status messages update in real-time

## 🧪 Test with Different Videos

Try different input videos to see how the mock detection varies:
- Short clips (< 30 seconds)
- Full match recordings
- Different resolutions

All will work with the mock detector!

## ⚙️ Customize Processing Parameters

Edit `backend/app.py` in the `@app.post("/api/process")` endpoint:

```python
# Current defaults:
window_size: int = 20      # Frames to check
threshold: int = 10         # Min detections needed
```

**Lower threshold** → More segments kept (less cutting)
**Higher threshold** → Fewer segments kept (more cutting)

## 🛑 Stop the Servers

- **Backend**: Press `Ctrl+C` in backend terminal
- **Frontend**: Press `Ctrl+C` in frontend terminal

## 🔄 Restart

Just re-run the same commands:

```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate && python app.py

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

## 📁 File Locations

- **Uploaded videos**: `backend/uploads/`
- **Processed videos**: `backend/uploads/` (named `*_processed.mp4`)
- **Temp segments**: `backend/temp_segments/`

To clean up:
- Use the "Clean Up Files" button in frontend, or
- Delete these directories manually

## 🤖 Next: Integrate Real YOLOv8 Model

When ready to use actual shuttlecock detection:

1. Collect badminton video dataset
2. Annotate frames with YOLO format
3. Train YOLOv8: `yolo detect train data.yaml epochs=100`
4. Update `backend/models/shuttlecock_detector.py` to use trained model
5. Replace mock detection with real inference

## 📞 API Quick Reference

```bash
# Upload
curl -F "file=@video.mp4" http://localhost:8000/api/upload

# Process
curl -X POST "http://localhost:8000/api/process?video_id=abc123"

# Check status
curl http://localhost:8000/api/status/job456

# Download
curl http://localhost:8000/api/download/abc123 > result.mp4

# Cleanup
curl -X DELETE http://localhost:8000/api/cleanup/abc123
```

## ✅ Checklist for First Run

- [ ] All prerequisites installed
- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Browser shows UI at http://localhost:3000
- [ ] Can upload a test video
- [ ] Processing status updates
- [ ] Can download result
- [ ] Can process another video

## 🎉 You're Ready!

The full-stack application is now running. You have:
- ✅ Frontend UI for uploads and downloads
- ✅ Backend FastAPI for video processing
- ✅ Mock detection pipeline (ready for real YOLOv8)
- ✅ Real-time status tracking
- ✅ Video cutting and stitching

Happy editing! 🏸
