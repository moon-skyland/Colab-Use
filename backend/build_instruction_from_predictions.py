"""Build edit instruction JSON from state predictions CSV."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from backend.model.common.schemas import StateSegment
    from backend.model.editing.instruction_utils import (
        save_edit_instruction,
        validate_edit_instruction,
    )
    from backend.model.editing.instruction_generator import InstructionGenerator
    from backend.model.segmentation.timeline_builder import TimelineBuilder
except ImportError:
    # Fallback for running as: python backend/build_instruction_from_predictions.py
    from model.common.schemas import StateSegment
    from model.editing.instruction_utils import (
        save_edit_instruction,
        validate_edit_instruction,
    )
    from model.editing.instruction_generator import InstructionGenerator
    from model.segmentation.timeline_builder import TimelineBuilder


def build_instruction_from_predictions(
    predictions_csv_path: str,
    video_path: str,
    output_video_path: str,
    timeline_output_path: str,
    instruction_output_path: str,
    min_segment_duration: float = 1.0,
    pre_roll: float = 1.0,
    post_roll: float = 0.5,
    min_keep_duration: float = 1.0,
    merge_gap: float = 0.5,
) -> str:
    """Build state timeline and edit instruction from prediction CSV."""
    predictions_path = Path(predictions_csv_path)
    if not predictions_path.exists():
        raise FileNotFoundError(
            f"Predictions CSV not found: {predictions_csv_path}"
        )

    builder = TimelineBuilder()
    timeline_json_path = builder.build_from_predictions_csv(
        predictions_csv_path=str(predictions_path),
        output_json_path=timeline_output_path,
        min_duration_seconds=min_segment_duration,
    )

    timeline_payload = json.loads(Path(timeline_json_path).read_text(encoding="utf-8"))
    segments = timeline_payload.get("segments", [])
    timeline = [
        StateSegment(
            start=float(item["start"]),
            end=float(item["end"]),
            state=str(item["state"]),
            confidence=(
                float(item["confidence"]) if item.get("confidence") is not None else None
            ),
        )
        for item in segments
    ]

    generator = InstructionGenerator()
    instruction = generator.generate(
        video_path=video_path,
        output_path=output_video_path,
        timeline=timeline,
        pre_roll_seconds=pre_roll,
        post_roll_seconds=post_roll,
        min_keep_duration=min_keep_duration,
        merge_gap_seconds=merge_gap,
    )
    validate_edit_instruction(instruction)
    instruction_json_path = save_edit_instruction(
        instruction=instruction,
        json_path=instruction_output_path,
        settings={
            "pre_roll_seconds": pre_roll,
            "post_roll_seconds": post_roll,
            "min_keep_duration": min_keep_duration,
            "merge_gap_seconds": merge_gap,
        },
    )

    instruction_payload = json.loads(
        Path(instruction_json_path).read_text(encoding="utf-8")
    )
    keep_intervals = instruction_payload.get("keep_intervals", [])

    print("Instruction build summary:")
    print(f"- predictions path: {predictions_path}")
    print(f"- timeline output path: {timeline_json_path}")
    print(f"- instruction output path: {instruction_json_path}")
    print(f"- number of timeline segments: {len(segments)}")
    print(f"- number of keep intervals: {len(keep_intervals)}")
    print("- keep intervals list:")
    for item in keep_intervals:
        print(
            f"  - {float(item['start']):.3f} -> "
            f"{float(item['end']):.3f} ({item.get('reason')})"
        )

    return str(instruction_json_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate edit instruction JSON from state predictions CSV."
    )
    parser.add_argument(
        "--predictions",
        default="backend/outputs/state_predictions.csv",
        help="Path to state predictions CSV.",
    )
    parser.add_argument(
        "--video",
        default="data/raw_videos/sample.mp4",
        help="Input raw video path.",
    )
    parser.add_argument(
        "--output-video",
        default="backend/outputs/edited_video.mp4",
        help="Planned edited video output path.",
    )
    parser.add_argument(
        "--timeline-output",
        default="backend/outputs/state_timeline.json",
        help="Output path for generated timeline JSON.",
    )
    parser.add_argument(
        "--instruction-output",
        default="backend/outputs/edit_instruction.json",
        help="Output path for generated edit instruction JSON.",
    )
    parser.add_argument(
        "--min-segment-duration",
        type=float,
        default=1.0,
        help="Minimum segment duration for timeline smoothing.",
    )
    parser.add_argument(
        "--pre-roll",
        type=float,
        default=1.0,
        help="Seconds before rally to include.",
    )
    parser.add_argument(
        "--post-roll",
        type=float,
        default=0.5,
        help="Seconds after rally to include.",
    )
    parser.add_argument(
        "--min-keep-duration",
        type=float,
        default=1.0,
        help="Minimum keep interval duration.",
    )
    parser.add_argument(
        "--merge-gap",
        type=float,
        default=0.5,
        help="Maximum gap to merge adjacent keep intervals.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        build_instruction_from_predictions(
            predictions_csv_path=args.predictions,
            video_path=args.video,
            output_video_path=args.output_video,
            timeline_output_path=args.timeline_output,
            instruction_output_path=args.instruction_output,
            min_segment_duration=args.min_segment_duration,
            pre_roll=args.pre_roll,
            post_roll=args.post_roll,
            min_keep_duration=args.min_keep_duration,
            merge_gap=args.merge_gap,
        )
    except Exception as exc:
        print(f"Failed to build instruction from predictions: {exc}")


if __name__ == "__main__":
    main()
