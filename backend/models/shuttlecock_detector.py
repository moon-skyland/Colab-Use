"""
Shuttlecock detection module using YOLOv8.

For now, this is a mock implementation. 
Later, you can replace the detect_frame() method with real YOLOv8 inference.
"""
import random
import numpy as np


class ShuttlecockDetector:
    """Mock shuttlecock detector for demo purposes."""
    
    def __init__(self, model_path: str = None):
        """
        Initialize the detector.
        
        Args:
            model_path: Path to the YOLOv8 model (not used in mock version)
        """
        self.model = None
        # TODO: Load actual YOLOv8 model here when ready
        # from ultralytics import YOLO
        # self.model = YOLO(model_path or "yolov8n.pt")
    
    def detect_frame(self, frame: np.ndarray) -> dict:
        """
        Detect shuttlecock in a single frame.
        
        Args:
            frame: OpenCV image frame (HxWx3 BGR array)
            
        Returns:
            dict with keys:
                - detected: bool, whether shuttlecock is detected
                - confidence: float, confidence score (0-1)
                - bbox: list [x1, y1, x2, y2] if detected, else None
        """
        # MOCK: Randomly simulate detection with ~60% base probability
        detected = random.random() < 0.6
        
        if detected:
            h, w = frame.shape[:2]
            # Simulate random bounding box in frame
            x1 = random.randint(0, w // 2)
            y1 = random.randint(0, h // 2)
            x2 = random.randint(w // 2, w)
            y2 = random.randint(h // 2, h)
            confidence = random.uniform(0.7, 0.99)
            bbox = [x1, y1, x2, y2]
        else:
            confidence = random.uniform(0, 0.3)
            bbox = None
        
        return {
            "detected": detected,
            "confidence": confidence,
            "bbox": bbox
        }
    
    def process_video(self, video_path: str, callback=None):
        """
        Process entire video frame-by-frame.
        
        Args:
            video_path: Path to the video file
            callback: Optional callback function(frame_idx, result) for progress tracking
            
        Returns:
            List of detection results for each frame
        """
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        results = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            result = self.detect_frame(frame)
            result["frame_idx"] = frame_idx
            results.append(result)
            
            if callback:
                callback(frame_idx, result)
            
            frame_idx += 1
        
        cap.release()
        return results
