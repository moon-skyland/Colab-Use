"""End-to-end backend pipeline runner for Part 5."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from backend.build_features_from_video import build_features_from_video
    from backend.build_instruction_from_predictions import build_instruction_from_predictions
    from backend.model.editing.cut_video import VideoCutter
    from backend.model.segmentation.state_predictor import StatePredictor
except ImportError:
    from build_features_from_video import build_features_from_video
    from build_instruction_from_predictions import build_instruction_from_predictions
    from model.editing.cut_video import VideoCutter
    from model.segmentation.state_predictor import StatePredictor


def run_full_pipeline(
    video_path: str,
    output_video_path: str,
    court_corners_json: str = "data/court_corners/sample_court_corners.json",
    max_frames: int = 0,
    window_size_seconds: float = 1.0,
) -> dict[str, object]:
    """Run full Part 5 processing pipeline from raw video to edited video."""
    features_csv = "data/features/features_inference.csv"
    predictions_csv = "backend/outputs/state_predictions.csv"
    timeline_json = "backend/outputs/state_timeline.json"
    instruction_json = "backend/outputs/edit_instruction.json"

    features_output = build_features_from_video(
        video_path=video_path,
        court_corners_json=court_corners_json,
        output_csv_path=features_csv,
        max_frames=max_frames,
        window_size_seconds=window_size_seconds,
    )
    if not features_output:
        raise RuntimeError(
            "Feature generation failed. Ensure court corners JSON is available."
        )

    predictor = StatePredictor(mock_if_missing=True)
    predictions_output = predictor.predict_csv(
        features_csv_path=features_output,
        output_csv_path=predictions_csv,
    )

    instruction_output = build_instruction_from_predictions(
        predictions_csv_path=predictions_output,
        video_path=video_path,
        output_video_path=output_video_path,
        timeline_output_path=timeline_json,
        instruction_output_path=instruction_json,
        min_segment_duration=1.0,
        pre_roll=1.0,
        post_roll=0.5,
        min_keep_duration=1.0,
        merge_gap=0.5,
    )

    cutter = VideoCutter()
    edited_path = cutter.cut_from_instruction_json(instruction_output)

    return {
        "features_csv": features_output,
        "predictions_csv": predictions_output,
        "timeline_json": timeline_json,
        "instruction_json": instruction_output,
        "edited_video": edited_path,
        "edited_exists": Path(edited_path).exists(),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full badminton backend pipeline.")
    parser.add_argument(
        "--video",
        default="data/raw_videos/sample.mp4",
        help="Input raw video path.",
    )
    parser.add_argument(
        "--output-video",
        default="backend/outputs/edited_video.mp4",
        help="Output edited video path.",
    )
    parser.add_argument(
        "--court-corners-json",
        default="data/court_corners/sample_court_corners.json",
        help="Court corners JSON path.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="0 for full video, >0 for first N frames.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_full_pipeline(
        video_path=args.video,
        output_video_path=args.output_video,
        court_corners_json=args.court_corners_json,
        max_frames=args.max_frames,
        window_size_seconds=1.0,
    )
    print("Full pipeline completed.")
    for key, value in result.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
