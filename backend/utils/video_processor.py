"""
Video processing utilities for smoothing, interval extraction, and video cutting.
"""
import cv2
import os
from typing import List, Tuple, Dict


def smooth_detections(
    detections: List[Dict],
    window_size: int = 20,
    threshold: int = 10
) -> List[int]:
    """
    Smooth frame-level detection results using sliding window.
    
    Args:
        detections: List of detection results (each with 'detected' key)
        window_size: Size of sliding window
        threshold: Minimum number of detections in window to mark as valid
        
    Returns:
        List of 0/1 labels for each frame (1 = valid rally segment)
    """
    labels = [1 if d.get("detected", False) else 0 for d in detections]
    smoothed = [0] * len(labels)
    
    for i in range(len(labels)):
        start = max(0, i - window_size // 2)
        end = min(len(labels), i + window_size // 2 + 1)
        window = labels[start:end]
        
        if sum(window) >= threshold:
            smoothed[i] = 1
        else:
            smoothed[i] = 0
    
    return smoothed


def extract_intervals(labels: List[int]) -> List[Tuple[int, int]]:
    """
    Extract continuous intervals from labeled frames.
    
    Args:
        labels: List of 0/1 labels for each frame
        
    Returns:
        List of (start_frame, end_frame) tuples for valid segments
    """
    intervals = []
    start = None
    
    for i, label in enumerate(labels):
        if label == 1 and start is None:
            start = i
        elif label == 0 and start is not None:
            intervals.append((start, i - 1))
            start = None
    
    if start is not None:
        intervals.append((start, len(labels) - 1))
    
    return intervals


def get_video_properties(video_path: str) -> Dict:
    """Get video properties like FPS, resolution, total frames."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    
    return {
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration_seconds": frame_count / fps if fps > 0 else 0
    }


def extract_video_segment(
    input_path: str,
    output_path: str,
    start_frame: int,
    end_frame: int,
    fps: float
) -> bool:
    """Extract a single video segment."""
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {input_path}")
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = cv2.VideoWriter_fourcc(*"mp4v")
    
    out = cv2.VideoWriter(output_path, codec, fps, (width, height))
    
    if not out.isOpened():
        cap.release()
        raise ValueError(f"Cannot create output video: {output_path}")
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    frame_idx = start_frame
    while frame_idx <= end_frame:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        out.write(frame)
        frame_idx += 1
    
    cap.release()
    out.release()
    
    return True


def concatenate_videos(segment_paths: List[str], output_path: str, fps: float) -> bool:
    """
    Concatenate multiple video segments into a single video.
    
    Args:
        segment_paths: List of paths to video segments
        output_path: Path for the output concatenated video
        fps: Frames per second for output video
        
    Returns:
        True if successful
    """
    if not segment_paths:
        raise ValueError("No segments to concatenate")
    
    # Get first frame to determine dimensions
    cap = cv2.VideoCapture(segment_paths[0])
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # Create output video
    codec = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, codec, fps, (width, height))
    
    if not out.isOpened():
        raise ValueError(f"Cannot create output video: {output_path}")
    
    # Write all segments
    for segment_path in segment_paths:
        cap = cv2.VideoCapture(segment_path)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            out.write(frame)
        
        cap.release()
    
    out.release()
    return True


def process_video_pipeline(
    input_path: str,
    output_path: str,
    detections: List[Dict],
    window_size: int = 20,
    threshold: int = 10,
    temp_dir: str = "./temp_segments"
) -> Dict:
    """
    Full pipeline: detect -> smooth -> extract intervals -> cut and stitch.
    
    Args:
        input_path: Path to input video
        output_path: Path to output edited video
        detections: List of frame detection results
        window_size: Sliding window size
        threshold: Detection threshold
        temp_dir: Directory for temporary segment files
        
    Returns:
        Dict with processing results
    """
    # Ensure temp directory exists
    os.makedirs(temp_dir, exist_ok=True)
    
    # Get video properties
    props = get_video_properties(input_path)
    fps = props["fps"]
    
    # Step 1: Smooth detections
    smoothed_labels = smooth_detections(detections, window_size, threshold)
    
    # Step 2: Extract intervals
    intervals = extract_intervals(smoothed_labels)
    
    if not intervals:
        return {
            "success": False,
            "error": "No valid rally segments found",
            "intervals": []
        }
    
    # Step 3: Extract and save segments
    segment_paths = []
    for idx, (start_frame, end_frame) in enumerate(intervals):
        segment_path = os.path.join(temp_dir, f"segment_{idx}.mp4")
        extract_video_segment(input_path, segment_path, start_frame, end_frame, fps)
        segment_paths.append(segment_path)
    
    # Step 4: Concatenate segments
    concatenate_videos(segment_paths, output_path, fps)
    
    # Clean up temp files
    for segment_path in segment_paths:
        if os.path.exists(segment_path):
            os.remove(segment_path)
    
    return {
        "success": True,
        "intervals": intervals,
        "segment_count": len(intervals),
        "original_frames": len(detections),
        "output_path": output_path
    }
