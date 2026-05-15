"""Build inference features CSV from a raw badminton video.

Pipeline:
Raw Video
-> frame iteration
-> athlete/shuttlecock detection
-> athlete/shuttlecock tracking
-> court mapping (manual corners + homography)
-> court position conversion
-> feature extraction
-> features_inference.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from backend.model.common.video_utils import get_video_info, iter_video_frames
    from backend.model.features import FeatureExtractor, write_feature_rows
    from backend.model.mapping import CourtMapper, CourtPositionConverter
    from backend.model.tracking import AthleteTracker, ShuttlecockTracker
    from backend.model.vision import AthleteDetector, ShuttlecockDetector
except ImportError:
    # Fallback when running with `python backend/build_features_from_video.py`
    from model.common.video_utils import get_video_info, iter_video_frames
    from model.features import FeatureExtractor, write_feature_rows
    from model.mapping import CourtMapper, CourtPositionConverter
    from model.tracking import AthleteTracker, ShuttlecockTracker
    from model.vision import AthleteDetector, ShuttlecockDetector


def build_features_from_video(
    video_path: str,
    court_corners_json: str,
    output_csv_path: str,
    max_frames: int = 0,
    window_size_seconds: float = 1.0,
) -> str:
    """Run Part 2->Part 3 integration to produce features_inference.csv."""
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    video_info = get_video_info(str(video_file))
    fps = float(video_info["fps"])
    if fps <= 0:
        raise ValueError(f"Invalid video fps ({fps}) from: {video_path}")

    corners_file = Path(court_corners_json)
    if not corners_file.exists():
        print(
            "Missing court corner JSON. Please create "
            "data/court_corners/sample_court_corners.json"
        )
        return ""

    payload = json.loads(corners_file.read_text(encoding="utf-8"))
    image_points_raw = payload.get("image_points")
    if not isinstance(image_points_raw, list) or len(image_points_raw) != 4:
        raise ValueError(
            "Court corners JSON must contain exactly 4 points in 'image_points'."
        )
    image_points = [
        (float(point[0]), float(point[1])) for point in image_points_raw
    ]

    court_mapper = CourtMapper()
    court_mapper.calibrate(image_points=image_points)

    athlete_detector = AthleteDetector()
    athlete_tracker = AthleteTracker()
    shuttle_detector = ShuttlecockDetector()
    shuttle_tracker = ShuttlecockTracker()

    all_athlete_tracks = []
    all_shuttle_tracks = []
    frames_processed = 0

    for frame_index, frame in iter_video_frames(str(video_file)):
        if max_frames > 0 and frame_index >= max_frames:
            break

        athlete_detections = athlete_detector.detect_frame(frame, frame_index)
        athlete_tracks = athlete_tracker.update(athlete_detections)
        all_athlete_tracks.extend(athlete_tracks)

        shuttle_detections = shuttle_detector.detect_frame(frame, frame_index)
        shuttle_track = shuttle_tracker.update(shuttle_detections, frame_index)
        all_shuttle_tracks.append(shuttle_track)

        frames_processed += 1

    converter = CourtPositionConverter()
    athlete_court_positions = converter.convert_athletes(
        athlete_tracks=all_athlete_tracks,
        court_mapper=court_mapper,
    )
    shuttle_court_positions = converter.convert_shuttlecock(
        shuttle_tracks=all_shuttle_tracks,
        court_mapper=court_mapper,
    )

    extractor = FeatureExtractor()
    feature_rows = extractor.extract_features(
        video_name=video_file.name,
        athlete_positions=athlete_court_positions,
        shuttlecock_positions=shuttle_court_positions,
        fps=fps,
        window_size_seconds=window_size_seconds,
    )

    if not feature_rows:
        print("Warning: no feature rows were generated from this run.")

    output_path = write_feature_rows(feature_rows, output_csv_path)

    print("Build features from video summary:")
    print(f"- video path: {video_file}")
    print(f"- fps: {fps}")
    print(f"- frames processed: {frames_processed}")
    print(f"- athlete track points: {len(all_athlete_tracks)}")
    print(f"- shuttlecock track points: {len(all_shuttle_tracks)}")
    print(f"- athlete court positions: {len(athlete_court_positions)}")
    print(f"- shuttlecock court positions: {len(shuttle_court_positions)}")
    print(f"- feature rows generated: {len(feature_rows)}")
    print(f"- output csv path: {output_path}")
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build inference feature CSV from raw video."
    )
    parser.add_argument(
        "--video",
        default="data/raw_videos/sample.mp4",
        help="Input raw video path.",
    )
    parser.add_argument(
        "--court-corners-json",
        default="data/court_corners/sample_court_corners.json",
        help="Court corners JSON file path.",
    )
    parser.add_argument(
        "--output",
        default="data/features/features_inference.csv",
        help="Output features CSV path.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="0 for full video, >0 for first N frames only.",
    )
    parser.add_argument(
        "--window-size",
        type=float,
        default=1.0,
        help="Feature window size in seconds.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        build_features_from_video(
            video_path=args.video,
            court_corners_json=args.court_corners_json,
            output_csv_path=args.output,
            max_frames=args.max_frames,
            window_size_seconds=args.window_size,
        )
    except Exception as exc:
        print(f"Failed to build features from video: {exc}")


if __name__ == "__main__":
    main()
