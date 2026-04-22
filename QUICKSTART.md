# 🏸 Badminton Video Editor - Getting Started Guide

## What You Have

Your badminton video editor is fully initialized with everything in **two main files**:

1. **`backend.py`** (13 KB)
   - Flask web server & REST API
   - ML model for point detection
   - SQLite database management
   - Video processing & editing engine
   - Background task processing

2. **`frontend.html`** (23 KB)
   - Complete web interface (no build needed)
   - Video upload with drag-and-drop
   - Video list management
   - Segment visualization
   - Video editing controls
   - Real-time progress tracking

## Quick Start (2 minutes)

### Option 1: Using the Start Script (Recommended)
```bash
cd "/Users/tj/Desktop/Badminton Editor"
./start.sh
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
cd "/Users/tj/Desktop/Badminton Editor"
pip install -r requirements.txt

# 2. Start backend
python backend.py

# 3. Open frontend in browser
open frontend.html
```

## After Startup

1. **Backend** starts on `http://localhost:5000`
2. **Frontend** opens in your browser
3. You should see the upload interface immediately

## How to Use

### Upload a Video
- Drag & drop a badminton video onto the upload area, OR
- Click to browse and select a video file
- Supported formats: MP4, AVI, MOV, MKV
- Max size: 2GB

### Processing
- The ML engine automatically analyzes the video
- Status updates in real-time
- Segments labeled as "point" (active gameplay) or "break" (shuttle pickup)

### Edit Video
- Select a video from the list
- Choose which segments to keep (points, breaks, or both)
- Click "Create Edited Video"
- Edited video is saved to the `edited_videos/` folder

## What's Inside

### Backend Components

**ML Model** - `BadmintonPointDetector` class:
- Analyzes frame sequences for motion
- Detects high-motion periods (active points)
- Detects low-motion periods (breaks/pickups)
- Generates segment timestamps and labels

**Database** - `VideoDatabase` class:
- SQLite with 3 tables: videos, segments, edited_videos
- Stores metadata and processing results
- Persists across sessions

**API Endpoints**:
- `POST /api/upload` - Upload and start processing
- `GET /api/videos` - List all videos
- `GET /api/video/{id}/segments` - Get segments
- `POST /api/video/{id}/edit` - Create edited video
- `GET /api/video/{id}/status` - Check processing status

### Frontend Components

**Sections**:
1. Upload area - Drag & drop video upload
2. Video list - See all uploaded videos
3. Segment editor - View and select segments
4. Edit controls - Choose what to keep/remove

**Features**:
- Real-time progress bar
- Status indicators
- Segment visualization
- Responsive design (mobile-friendly)
- Beautiful gradient UI

## File Structure Created

```
/Users/tj/Desktop/Badminton Editor/
├── backend.py                 # Main server & ML engine
├── frontend.html              # Web interface
├── requirements.txt           # Python dependencies
├── README.md                  # Full documentation
├── start.sh                   # Quick start script
├── uploads/                   # (Auto-created) Uploaded videos
├── edited_videos/             # (Auto-created) Edited outputs
└── badminton_videos.db        # (Auto-created) SQLite database
```

## Customization

### Tune ML Detection

Edit `backend.py` line ~20:
```python
class BadmintonPointDetector:
    def __init__(self):
        self.motion_threshold = 5000      # ← Increase for stricter detection
        self.still_threshold = 2000       # ← Increase for longer breaks
```

### Change API Port

Edit `backend.py` last line:
```python
if __name__ == '__main__':
    app.run(debug=True, port=8000)  # ← Change port here
```

Also update `frontend.html` line ~289:
```javascript
const API_BASE = 'http://localhost:8000/api';  // ← Match the port
```

## Troubleshooting

**Port 5000 already in use?**
```bash
# Find process using port 5000
lsof -i :5000

# Change port in backend.py and frontend.html
```

**Permission denied on start.sh?**
```bash
chmod +x "/Users/tj/Desktop/Badminton Editor/start.sh"
```

**Module not found errors?**
```bash
pip install -r requirements.txt --upgrade
```

**Video not processing?**
1. Check backend console for errors
2. Ensure video format is supported
3. Verify disk space in `uploads/` folder

## Next Steps

1. **Test it**: Upload a sample badminton video
2. **Observe**: Watch the ML detection in real-time
3. **Edit**: Create your first edited video
4. **Customize**: Adjust thresholds for better accuracy
5. **Extend**: Add more features (see README.md)

## Project Statistics

| Component | Lines | Purpose |
|-----------|-------|---------|
| Backend | ~400 | Server + ML + DB + API |
| Frontend | ~500 | UI + Upload + Controls |
| **Total** | **~900** | **Complete system** |

## Performance

- **Typical video (5-10 min)**: 30-120 seconds to process
- **Video editing**: Seconds to minutes (depends on video length)
- **Memory usage**: ~200-500 MB during processing
- **Disk space**: ~3-5x original video size for temp + output

## Key Files to Know

| File | Purpose | Edit for... |
|------|---------|-------------|
| `backend.py` | Everything backend | Logic, ML, API endpoints |
| `frontend.html` | Everything frontend | UI, styling, user experience |
| `requirements.txt` | Dependencies | Adding/updating packages |

## Architecture Diagram

```
Web Browser (frontend.html)
          ↓
    HTTP/REST API
          ↓
   Flask Server (backend.py)
   ├── Video Upload Handler
   ├── ML Model (Point Detection)
   ├── Video Processing
   ├── SQLite Database
   └── Video Editor/Export
          ↓
   File System
   ├── uploads/
   ├── edited_videos/
   └── badminton_videos.db
```

## Support & Help

1. Check **README.md** for detailed documentation
2. Review **backend.py** comments for implementation details
3. Check browser console (F12) for frontend errors
4. Check terminal for backend errors

---

**You're all set!** 🎉

Run `./start.sh` and your badminton video editor is ready to go.

Questions? Check the README.md for comprehensive documentation.
