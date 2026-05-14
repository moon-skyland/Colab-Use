"""Unified backend pipeline orchestration for video processing."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from backend.build_features_from_video import build_features_from_video
    from backend.model.common.schemas import StateSegment
    from backend.model.editing.cut_video import VideoCutter
    from backend.model.editing.instruction_generator import InstructionGenerator
    from backend.model.editing.instruction_utils import save_edit_instruction
    from backend.model.segmentation.state_predictor import StatePredictor
    from backend.model.segmentation.timeline_builder import TimelineBuilder
except ImportError:
    from build_features_from_video import build_features_from_video
    from model.common.schemas import StateSegment
    from model.editing.cut_video import VideoCutter
    from model.editing.instruction_generator import InstructionGenerator
    from model.editing.instruction_utils import save_edit_instruction
    from model.segmentation.state_predictor import StatePredictor
    from model.segmentation.timeline_builder import TimelineBuilder


def process_video_pipeline(
    video_path: str,
    court_corners_json: str | None = None,
    output_dir: str = "backend/outputs",
    max_frames: int = 0,
    window_size_seconds: float = 1.0,
    use_mock_if_missing: bool = True,
) -> dict:
    """Run the full backend pipeline for one input video.

    Flow:
    A) Build features from video
    B) Predict states
    C) Build timeline + edit instruction
    D) Cut edited video
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    features_csv = output_path / "features_inference.csv"
    predictions_csv = output_path / "state_predictions.csv"
    timeline_json = output_path / "state_timeline.json"
    instruction_json = output_path / "edit_instruction.json"
    edited_video = output_path / "edited_video.mp4"

    warnings: list[str] = []

    try:
        video_file = Path(video_path)
        if not video_file.exists():
            raise FileNotFoundError(f"Input video not found: {video_path}")

        corners_path = (
            Path(court_corners_json)
            if court_corners_json
            else Path("backend/data/court_corners/sample_court_corners.json")
        )
        if not corners_path.exists():
            if court_corners_json:
                raise FileNotFoundError(
                    f"Court corners JSON not found: {court_corners_json}"
                )
            raise FileNotFoundError(
                "Missing court corner JSON. Provide --court-corners-json or create "
                "backend/data/court_corners/sample_court_corners.json"
            )
        if court_corners_json is None:
            warnings.append(
                "Using placeholder court corners JSON for development."
            )

        built_features = build_features_from_video(
            video_path=str(video_file),
            court_corners_json=str(corners_path),
            output_csv_path=str(features_csv),
            max_frames=max_frames,
            window_size_seconds=window_size_seconds,
        )
        if not built_features:
            raise RuntimeError(
                "Feature generation returned empty output path."
            )

        predictor = StatePredictor(
            model_path="backend/models/state_model.pkl",
            metadata_path="backend/models/state_model_metadata.json",
            mock_if_missing=use_mock_if_missing,
        )
        predictor.predict_csv(
            features_csv_path=str(features_csv),
            output_csv_path=str(predictions_csv),
        )

        builder = TimelineBuilder()
        builder.build_from_predictions_csv(
            predictions_csv_path=str(predictions_csv),
            output_json_path=str(timeline_json),
            min_duration_seconds=1.0,
        )

        timeline_payload = json.loads(timeline_json.read_text(encoding="utf-8"))
        segment_items = timeline_payload.get("segments", [])
        timeline_segments = [
            StateSegment(
                start=float(item["start"]),
                end=float(item["end"]),
                state=str(item["state"]),
                confidence=(
                    float(item["confidence"])
                    if item.get("confidence") is not None
                    else None
                ),
            )
            for item in segment_items
        ]

        generator = InstructionGenerator()
        instruction = generator.generate(
            video_path=str(video_file),
            output_path=str(edited_video),
            timeline=timeline_segments,
            pre_roll_seconds=1.0,
            post_roll_seconds=0.5,
            min_keep_duration=1.0,
            merge_gap_seconds=0.5,
        )
        save_edit_instruction(
            instruction=instruction,
            json_path=str(instruction_json),
            settings={
                "pre_roll_seconds": 1.0,
                "post_roll_seconds": 0.5,
                "min_keep_duration": 1.0,
                "merge_gap_seconds": 0.5,
            },
        )

        cutter = VideoCutter()
        cutter.cut_from_instruction_json(str(instruction_json))

        return {
            "original_video": str(video_file),
            "features_csv": str(features_csv),
            "state_predictions_csv": str(predictions_csv),
            "state_timeline_json": str(timeline_json),
            "edit_instruction_json": str(instruction_json),
            "edited_video": str(edited_video),
            "status": "success",
            "warnings": warnings,
        }
    except Exception as exc:
        return {
            "original_video": video_path,
            "features_csv": str(features_csv),
            "state_predictions_csv": str(predictions_csv),
            "state_timeline_json": str(timeline_json),
            "edit_instruction_json": str(instruction_json),
            "edited_video": str(edited_video),
            "status": "failed",
            "error": str(exc),
            "warnings": warnings,
        }
