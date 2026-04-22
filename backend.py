"""
Badminton Video Editor - Backend
ML-powered video editor that recognizes badminton points and breaks
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading

# ==================== ML MODEL ====================
class BadmintonPointDetector:
    """
    Machine Learning model for detecting badminton points.
    Uses motion detection and frame analysis to identify:
    - Point in progress (high motion, players in action)
    - Point ended (still frames, pickup period)
    """
    
    def __init__(self):
        self.motion_threshold = 5000
        self.still_threshold = 2000
        self.frame_buffer = []
        self.buffer_size = 30
        
    def detect_motion(self, frame1, frame2):
        """Detect motion between two frames using optical flow."""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        motion_score = np.sum(diff)
        return motion_score
    
    def analyze_frame_sequence(self, frames):
        """Analyze sequence of frames to detect point start/end."""
        if len(frames) < 2:
            return None
        
        motion_scores = []
        for i in range(1, len(frames)):
            score = self.detect_motion(frames[i-1], frames[i])
            motion_scores.append(score)
        
        avg_motion = np.mean(motion_scores)
        is_point_active = avg_motion > self.motion_threshold
        
        return {
            'is_active': is_point_active,
            'motion_score': avg_motion,
            'motion_scores': motion_scores
        }
    
    def process_video(self, video_path, callback=None):
        """
        Process video file and detect point boundaries.
        Returns list of segments with start/end times and labels.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        segments = []
        frame_count = 0
        prev_state = None
        segment_start = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize for faster processing
            frame = cv2.resize(frame, (640, 480))
            self.frame_buffer.append(frame)
            
            if len(self.frame_buffer) > self.buffer_size:
                self.frame_buffer.pop(0)
            
            if len(self.frame_buffer) >= 5:
                analysis = self.analyze_frame_sequence(self.frame_buffer[-5:])
                current_state = 'point' if analysis['is_active'] else 'break'
                
                if prev_state != current_state:
                    if prev_state is not None:
                        segments.append({
                            'start_frame': segment_start,
                            'end_frame': frame_count,
                            'start_time': segment_start / fps,
                            'end_time': frame_count / fps,
                            'label': prev_state
                        })
                    segment_start = frame_count
                    prev_state = current_state
            
            frame_count += 1
            progress = (frame_count / total_frames) * 100
            
            if callback:
                callback(progress, frame_count, total_frames)
        
        # Add final segment
        if prev_state:
            segments.append({
                'start_frame': segment_start,
                'end_frame': frame_count,
                'start_time': segment_start / fps,
                'end_time': frame_count / fps,
                'label': prev_state
            })
        
        cap.release()
        return segments


# ==================== DATABASE ====================
class VideoDatabase:
    """SQLite database for storing videos and segments."""
    
    def __init__(self, db_path='badminton_videos.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_path TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration REAL,
                fps REAL,
                status TEXT DEFAULT 'uploaded'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                start_frame INTEGER,
                end_frame INTEGER,
                start_time REAL,
                end_time REAL,
                label TEXT,
                duration REAL,
                FOREIGN KEY(video_id) REFERENCES videos(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edited_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                output_path TEXT,
                edit_type TEXT,
                segments_included TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(video_id) REFERENCES videos(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_video(self, filename, path, duration, fps):
        """Add video record to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO videos (filename, original_path, duration, fps)
            VALUES (?, ?, ?, ?)
        ''', (filename, path, duration, fps))
        conn.commit()
        video_id = cursor.lastrowid
        conn.close()
        return video_id
    
    def add_segments(self, video_id, segments):
        """Add detected segments to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for segment in segments:
            cursor.execute('''
                INSERT INTO segments 
                (video_id, start_frame, end_frame, start_time, end_time, label, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                segment['start_frame'],
                segment['end_frame'],
                segment['start_time'],
                segment['end_time'],
                segment['label'],
                segment['end_time'] - segment['start_time']
            ))
        conn.commit()
        conn.close()
    
    def get_video_segments(self, video_id):
        """Get all segments for a video."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, start_time, end_time, label, duration FROM segments
            WHERE video_id = ? ORDER BY start_time
        ''', (video_id,))
        segments = cursor.fetchall()
        conn.close()
        return segments
    
    def get_all_videos(self):
        """Get all videos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, filename, upload_date, duration, status FROM videos
            ORDER BY upload_date DESC
        ''')
        videos = cursor.fetchall()
        conn.close()
        return videos


# ==================== FLASK APP ====================
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
EDITED_FOLDER = 'edited_videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EDITED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB max

db = VideoDatabase()
detector = BadmintonPointDetector()

processing_status = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Badminton Editor Backend Running'})


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload and process badminton video."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Get video metadata
    cap = cv2.VideoCapture(filepath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    cap.release()
    
    # Add to database
    video_id = db.add_video(filename, filepath, duration, fps)
    processing_status[video_id] = {'progress': 0, 'status': 'queued'}
    
    # Start processing in background
    thread = threading.Thread(target=process_video_background, args=(video_id, filepath))
    thread.start()
    
    return jsonify({
        'video_id': video_id,
        'filename': filename,
        'duration': duration,
        'fps': fps,
        'status': 'processing'
    }), 202


def process_video_background(video_id, filepath):
    """Background processing of video."""
    try:
        processing_status[video_id]['status'] = 'processing'
        
        def progress_callback(progress, frame, total):
            processing_status[video_id]['progress'] = progress
        
        segments = detector.process_video(filepath, progress_callback)
        db.add_segments(video_id, segments)
        
        processing_status[video_id]['status'] = 'completed'
        processing_status[video_id]['segments'] = segments
    except Exception as e:
        processing_status[video_id]['status'] = 'error'
        processing_status[video_id]['error'] = str(e)


@app.route('/api/videos', methods=['GET'])
def get_videos():
    """Get all uploaded videos."""
    videos = db.get_all_videos()
    return jsonify([{
        'id': v[0],
        'filename': v[1],
        'upload_date': v[2],
        'duration': v[3],
        'status': v[4]
    } for v in videos])


@app.route('/api/video/<int:video_id>/segments', methods=['GET'])
def get_segments(video_id):
    """Get detected segments for a video."""
    segments = db.get_video_segments(video_id)
    return jsonify([{
        'id': s[0],
        'start_time': s[1],
        'end_time': s[2],
        'label': s[3],
        'duration': s[4]
    } for s in segments])


@app.route('/api/video/<int:video_id>/status', methods=['GET'])
def get_status(video_id):
    """Get processing status of a video."""
    status = processing_status.get(video_id, {'status': 'unknown'})
    return jsonify(status)


@app.route('/api/video/<int:video_id>/edit', methods=['POST'])
def edit_video(video_id):
    """Create edited video keeping only points (remove breaks)."""
    data = request.get_json()
    keep_labels = data.get('keep_labels', ['point'])
    
    segments = db.get_video_segments(video_id)
    videos = db.get_all_videos()
    video = next((v for v in videos if v[0] == video_id), None)
    
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    original_path = video[2]
    cap = cv2.VideoCapture(original_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    output_filename = f"edited_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    output_path = os.path.join(EDITED_FOLDER, output_filename)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_num = 0
    for start_time, end_time, label, duration in segments:
        if label in keep_labels:
            cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                if current_time > end_time:
                    break
                out.write(frame)
    
    cap.release()
    out.release()
    
    return jsonify({
        'output_filename': output_filename,
        'output_path': output_path,
        'message': 'Video edited successfully'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
