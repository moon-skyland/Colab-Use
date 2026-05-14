"""Small Part 2 pipeline runner on synthetic frames.

This validates:
- Athlete Detector
- Athlete Tracker
- Shuttlecock Detector
- Shuttlecock Tracker
- Court Mapper
- Court Position Converter
"""

import cv2
import numpy as np

from model.mapping.court_mapper import CourtMapper
from model.mapping.court_position_converter import CourtPositionConverter
from model.tracking.athlete_tracker import AthleteTracker
from model.tracking.shuttlecock_tracker import ShuttlecockTracker
from model.vision.athlete_detector import AthleteDetector
from model.vision.shuttlecock_detector import ShuttlecockDetector


def _build_synthetic_frames(num_frames: int = 20) -> list[np.ndarray]:
    height, width = 720, 1280
    frames: list[np.ndarray] = []

    for idx in range(num_frames):
        frame = np.full((height, width, 3), (30, 130, 30), dtype=np.uint8)

        # Two moving "athletes" as dark upright rectangles.
        p1_x = 260 + idx * 3
        p2_x = 880 - idx * 2
        cv2.rectangle(frame, (p1_x, 380), (p1_x + 55, 620), (10, 10, 10), -1)
        cv2.rectangle(frame, (p2_x, 300), (p2_x + 60, 560), (15, 15, 15), -1)

        # Shuttlecock as a small bright point.
        shuttle_x = 200 + idx * 35
        shuttle_y = 180 + int(60 * np.sin(idx / 4.0))
        cv2.circle(frame, (shuttle_x, shuttle_y), 4, (255, 255, 255), -1)
        frames.append(frame)

    return frames


def run_part2_pipeline() -> None:
    frames = _build_synthetic_frames()

    athlete_detector = AthleteDetector()
    shuttlecock_detector = ShuttlecockDetector()
    athlete_tracker = AthleteTracker()
    shuttlecock_tracker = ShuttlecockTracker()

    mapper = CourtMapper()
    mapping_result = mapper.calibrate(
        [
            (160.0, 120.0),   # top-left
            (1120.0, 120.0),  # top-right
            (1180.0, 680.0),  # bottom-right
            (100.0, 680.0),   # bottom-left
        ]
    )
    converter = CourtPositionConverter()

    total_athlete_detections = 0
    visible_shuttle_count = 0

    for frame_index, frame in enumerate(frames):
        athlete_detections = athlete_detector.detect_frame(frame, frame_index)
        athlete_tracks = athlete_tracker.update(athlete_detections)

        shuttle_detections = shuttlecock_detector.detect_frame(frame, frame_index)
        shuttle_track = shuttlecock_tracker.update(shuttle_detections, frame_index)

        athlete_court_positions = converter.convert_athletes(athlete_tracks, mapper)
        shuttle_court_positions = converter.convert_shuttlecock([shuttle_track], mapper)
        shuttle_court_position = shuttle_court_positions[0]

        total_athlete_detections += len(athlete_detections)
        if shuttle_track.visible:
            visible_shuttle_count += 1

        if frame_index in {0, len(frames) - 1}:
            print(f"\nFrame {frame_index}")
            print(f"  athlete detections: {len(athlete_detections)}")
            print(f"  athlete tracks: {len(athlete_tracks)}")
            if athlete_court_positions:
                print(f"  sample athlete court pos: {athlete_court_positions[0]}")
            print(f"  shuttle visible: {shuttle_track.visible}")
            print(f"  shuttle court pos: {shuttle_court_position.ball_court}")

    print("\nPart 2 pipeline test completed.")
    print(f"Frames processed: {len(frames)}")
    print(f"Total athlete detections: {total_athlete_detections}")
    print(f"Shuttle visible frames: {visible_shuttle_count}")


if __name__ == "__main__":
    run_part2_pipeline()
