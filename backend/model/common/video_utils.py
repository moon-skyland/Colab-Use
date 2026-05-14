"""Basic video utilities for Part 2 pipeline tests."""

from pathlib import Path
from typing import Generator

import cv2
import numpy as np


def _validate_video_path(video_path: str) -> Path:
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")
    return path


def get_video_info(video_path: str) -> dict[str, float | int]:
    """Return video metadata: fps, frame_count, duration, width, height."""
    path = _validate_video_path(video_path)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"OpenCV failed to open video: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    capture.release()

    duration = (frame_count / fps) if fps > 0 else 0.0
    return {
        "fps": fps,
        "frame_count": frame_count,
        "duration": duration,
        "width": width,
        "height": height,
    }


def iter_video_frames(video_path: str) -> Generator[tuple[int, np.ndarray], None, None]:
    """Yield `(frame_index, frame)` pairs from a video."""
    path = _validate_video_path(video_path)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"OpenCV failed to open video: {video_path}")

    try:
        frame_index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            yield frame_index, frame
            frame_index += 1
    finally:
        capture.release()


def read_first_frame(video_path: str) -> np.ndarray:
    """Read and return the first frame from a video."""
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise FileNotFoundError(f"Unable to open video: {video_path}")

    ok, frame = capture.read()
    capture.release()
    if not ok or frame is None:
        raise ValueError(f"Video contains no readable frames: {video_path}")
    return frame


def ensure_dir(path: str) -> None:
    """Create directory path if it does not exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def save_first_frame(video_path: str, output_path: str) -> str:
    """Save the first frame of a video for court calibration."""
    path = _validate_video_path(video_path)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"OpenCV failed to open video: {video_path}")

    try:
        ok, frame = capture.read()
    finally:
        capture.release()

    if not ok or frame is None:
        raise ValueError(f"Could not read first frame from video: {video_path}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_ok = cv2.imwrite(str(output), frame)
    if not write_ok:
        raise ValueError(f"Failed to save first frame to: {output_path}")
    return str(output)
