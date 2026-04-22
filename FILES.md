# 📁 Project Files Reference

## Core Application (2 Files - Everything is Here!)

### 1. **backend.py** (407 lines)
Your complete backend in one file.

**Contains:**
- `BadmintonPointDetector` class - ML engine for point detection
  - `detect_motion()` - Calculate motion between frames
  - `analyze_frame_sequence()` - Analyze sequence of frames
  - `process_video()` - Main ML pipeline
  
- `VideoDatabase` class - SQLite database management
  - `init_db()` - Create tables
  - `add_video()` - Store video metadata
  - `add_segments()` - Store detected segments
  - `get_video_segments()` - Query segments
  - `get_all_videos()` - List videos

- Flask REST API routes
  - `/api/health` - Health check
  - `/api/upload` - Upload and process video
  - `/api/videos` - List all videos
  - `/api/video/{id}/segments` - Get segments
  - `/api/video/{id}/status` - Check status
  - `/api/video/{id}/edit` - Create edited video

- Background processing with threading
- Configuration and initialization

**How to edit:**
- Adjust ML thresholds: ~line 20
- Add new API endpoints: Add new @app.route decorators
- Tune ML algorithm: Modify `analyze_frame_sequence()` method
- Change server port: Last line (app.run)

---

### 2. **frontend.html** (774 lines)
Your complete web interface in one file.

**Contains:**
- HTML structure
  - Upload area (drag & drop)
  - Video list
  - Segment viewer
  - Editor controls
  
- CSS styling (~300 lines)
  - Modern gradient design
  - Responsive layout
  - Color scheme
  - Animations
  
- JavaScript logic (~200 lines)
  - API communication
  - File upload handling
  - Real-time progress
  - Video management
  - Segment rendering
  - Video editing

**How to edit:**
- Change colors: CSS section, search for #667eea
- Modify layout: Edit grid-template-columns in .content class
- Add new sections: Add new `<div class="card">` elements
- Change API URL: Line ~289, const API_BASE
- Add UI features: Edit HTML structure and JavaScript handlers

---

## Support Files

### **requirements.txt**
Python dependencies for backend.

**Current dependencies:**
```
flask==3.0.0           # Web framework
flask-cors==4.0.0      # Enable frontend access
numpy==1.24.3          # Array operations
opencv-python==4.8.0.76  # Video processing
werkzeug==3.0.0        # WSGI utilities
```

**To add more:**
```bash
pip install package_name
pip freeze > requirements.txt
```

---

### **start.sh**
One-command launcher script.

**Does:**
1. Check Python version
2. Install dependencies
3. Create upload/output folders
4. Start Flask backend
5. Shows helpful messages

**Make executable:**
```bash
chmod +x start.sh
```

---

### **README.md**
Comprehensive technical documentation.

**Includes:**
- Feature overview
- Installation instructions
- Architecture explanation
- ML algorithm details
- Database schema
- API reference
- Configuration guide
- Troubleshooting
- Deployment options

---

### **QUICKSTART.md**
5-minute getting started guide.

**For:** First-time users
**Contains:**
- Quick setup
- First run instructions
- Basic usage workflow
- Common issues

---

### **PROJECT_INDEX.md**
Detailed project overview and reference.

**Contains:**
- Complete file listing
- Feature descriptions
- API documentation
- Configuration options
- Performance info
- Troubleshooting guide

---

### **SUMMARY.txt**
Visual project summary (ASCII art).

**Shows:**
- Project structure
- Quick start commands
- Architecture diagram
- ML system explanation
- Statistics
- Next steps

---

### **FILES.md**
This file - complete file reference.

---

## Auto-Generated Directories

These are created automatically when the app runs:

### **uploads/**
Stores uploaded video files.
```
uploads/
├── video1.mp4
├── video2.avi
└── video3.mov
```

### **edited_videos/**
Stores edited/exported videos.
```
edited_videos/
├── edited_1_20260422_113000.mp4
├── edited_2_20260422_113500.mp4
└── edited_3_20260422_114000.mp4
```

### **badminton_videos.db**
SQLite database file.
Contains 3 tables:
- videos
- segments
- edited_videos

---

## File Size Reference

| File | Size | Benefit |
|------|------|---------|
| backend.py | 13 KB | Complete backend |
| frontend.html | 23 KB | Full web UI |
| requirements.txt | 85 B | Minimal dependencies |
| README.md | 7.8 KB | Full documentation |
| QUICKSTART.md | 6.0 KB | Quick guide |
| PROJECT_INDEX.md | 7.8 KB | Detailed reference |
| SUMMARY.txt | 11 KB | Visual guide |
| start.sh | 1.4 KB | Launcher script |
| FILES.md | This file | File reference |
| **TOTAL** | **~84 KB** | **Complete system** |

---

## Quick Edit Reference

### I want to...

**Change ML sensitivity:**
```
File: backend.py
Line: ~20
Find: self.motion_threshold = 5000
Change: Increase for stricter, decrease for looser detection
```

**Change server port:**
```
File: backend.py
Line: Last line
Find: app.run(debug=True, port=5000)
Change: port=XXXX to your port number

File: frontend.html
Line: ~289
Find: const API_BASE = 'http://localhost:5000/api'
Change: Port number to match backend
```

**Change UI colors:**
```
File: frontend.html
Line: CSS section (~50-250)
Find: #667eea (primary color) or #764ba2 (secondary)
Change: To your preferred colors
```

**Add new API endpoint:**
```
File: backend.py
Location: Below other @app.route decorators

@app.route('/api/new-endpoint', methods=['GET'])
def new_endpoint():
    return jsonify({'data': 'your data'})
```

**Disable background processing:**
```
File: backend.py
Line: In upload_video() function
Comment out: thread = threading.Thread(...)
             thread.start()
```

**Increase upload size limit:**
```
File: backend.py
Line: ~230
Find: app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024
Change: 2 to your desired number (in GB)
```

---

## Development Workflow

### Setup
```bash
cd "/Users/tj/Desktop/Badminton Editor"
pip install -r requirements.txt
```

### Run
```bash
python backend.py
# In browser: open frontend.html
```

### Edit
1. Make changes to backend.py or frontend.html
2. Restart backend (Ctrl+C, then python backend.py)
3. Refresh browser (Cmd+R or Ctrl+R)

### Deploy
```bash
# Docker
docker build -t badminton-editor .
docker run -p 5000:5000 badminton-editor

# Or traditional
pip install -r requirements.txt
python backend.py
```

---

## File Locations

```
/Users/tj/Desktop/Badminton Editor/
├── backend.py                 # ← Edit for backend changes
├── frontend.html              # ← Edit for UI/frontend changes
├── requirements.txt           # ← Edit to add dependencies
├── start.sh                   # ← Run to start everything
├── README.md                  # ← Read for documentation
├── QUICKSTART.md              # ← Read for quick start
├── PROJECT_INDEX.md           # ← Read for project overview
├── SUMMARY.txt                # ← Read for visual guide
├── FILES.md                   # ← You are here
├── uploads/                   # (created at runtime)
├── edited_videos/             # (created at runtime)
└── badminton_videos.db        # (created at runtime)
```

---

## Common Tasks

### Check server is running
```bash
curl http://localhost:5000/api/health
```

### View database
```bash
sqlite3 badminton_videos.db
.tables
SELECT * FROM videos;
.quit
```

### Delete all uploads
```bash
rm -rf uploads/*
rm -rf edited_videos/*
rm badminton_videos.db  # Will recreate on next run
```

### Change Python executable
In start.sh:
```bash
# Change from:
python backend.py

# To:
python3 backend.py
# or
/usr/bin/python3.11 backend.py
```

---

## What's Where

| Purpose | File |
|---------|------|
| **ML Engine** | backend.py (BadmintonPointDetector class) |
| **Database** | backend.py (VideoDatabase class) + badminton_videos.db |
| **Web Server** | backend.py (Flask routes) |
| **User Interface** | frontend.html (entire file) |
| **Styling** | frontend.html (CSS section) |
| **JavaScript Logic** | frontend.html (JavaScript section) |
| **Configuration** | backend.py (top of file) or frontend.html (line ~289) |
| **Dependencies** | requirements.txt |
| **Documentation** | README.md, QUICKSTART.md, PROJECT_INDEX.md |
| **Getting Started** | start.sh, this file |

---

## Next Steps

1. **Read:** QUICKSTART.md (5 minutes)
2. **Run:** `./start.sh`
3. **Test:** Upload a video
4. **Customize:** Edit backend.py or frontend.html
5. **Extend:** Add new features

---

Created: April 22, 2026
Everything in two files: **backend.py** + **frontend.html**
Ready to use: **Yes** ✅
