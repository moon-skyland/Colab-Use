"""Part 4 synthetic test: predictions -> timeline -> edit instruction."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from model.editing.instruction_generator import InstructionGenerator
from model.editing.instruction_utils import (
    load_edit_instruction,
    merge_intervals,
    save_edit_instruction,
    validate_edit_instruction,
)
from model.common.schemas import KeepInterval, StateSegment
from model.segmentation.timeline_builder import TimelineBuilder


PREDICTIONS_CSV_PATH = "backend/outputs/demo_state_predictions.csv"
TIMELINE_JSON_PATH = "backend/outputs/demo_state_timeline.json"
INSTRUCTION_JSON_PATH = "backend/outputs/demo_edit_instruction.json"


def _build_synthetic_predictions_csv(path: str) -> str:
    rows = [
        {"video": "demo.mp4", "start": 0.0, "end": 1.0, "predicted_state": "DEAD_TIME", "confidence": 0.93},
        {"video": "demo.mp4", "start": 1.0, "end": 2.0, "predicted_state": "DEAD_TIME", "confidence": 0.92},
        {"video": "demo.mp4", "start": 2.0, "end": 3.0, "predicted_state": "READY_TO_SERVE", "confidence": 0.81},
        {"video": "demo.mp4", "start": 3.0, "end": 4.0, "predicted_state": "RALLY_ACTIVE", "confidence": 0.95},
        {"video": "demo.mp4", "start": 4.0, "end": 5.0, "predicted_state": "RALLY_ACTIVE", "confidence": 0.96},
        {"video": "demo.mp4", "start": 5.0, "end": 6.0, "predicted_state": "RALLY_ENDING", "confidence": 0.84},
        {"video": "demo.mp4", "start": 6.0, "end": 7.0, "predicted_state": "DEAD_TIME", "confidence": 0.91},
        {"video": "demo.mp4", "start": 7.0, "end": 8.0, "predicted_state": "DEAD_TIME", "confidence": 0.90},
        {"video": "demo.mp4", "start": 8.0, "end": 9.0, "predicted_state": "READY_TO_SERVE", "confidence": 0.79},
        {"video": "demo.mp4", "start": 9.0, "end": 10.0, "predicted_state": "RALLY_ACTIVE", "confidence": 0.94},
        {"video": "demo.mp4", "start": 10.0, "end": 11.0, "predicted_state": "RALLY_ENDING", "confidence": 0.83},
        {"video": "demo.mp4", "start": 11.0, "end": 12.0, "predicted_state": "DEAD_TIME", "confidence": 0.92},
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    return str(out)


def main() -> None:
    predictions_path = _build_synthetic_predictions_csv(PREDICTIONS_CSV_PATH)

    builder = TimelineBuilder()
    timeline_path = builder.build_from_predictions_csv(
        predictions_csv_path=predictions_path,
        output_json_path=TIMELINE_JSON_PATH,
        min_duration_seconds=1.0,
    )

    timeline_data = json.loads(Path(timeline_path).read_text(encoding="utf-8"))
    segments = timeline_data.get("segments", [])
    timeline_segments = [
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
        video_path="data/raw_videos/demo.mp4",
        output_path="backend/outputs/demo_edited_video.mp4",
        timeline=timeline_segments,
        pre_roll_seconds=1.0,
        post_roll_seconds=0.5,
        min_keep_duration=1.0,
        merge_gap_seconds=0.5,
    )
    assert hasattr(instruction, "keep_intervals"), "Expected EditInstruction object."

    validate_edit_instruction(instruction)
    instruction_path = save_edit_instruction(
        instruction=instruction,
        json_path=INSTRUCTION_JSON_PATH,
        settings={
            "pre_roll_seconds": 1.0,
            "post_roll_seconds": 0.5,
            "min_keep_duration": 1.0,
            "merge_gap_seconds": 0.5,
        },
    )
    loaded_instruction = load_edit_instruction(instruction_path)
    validate_edit_instruction(loaded_instruction)
    keep_intervals = loaded_instruction.keep_intervals

    print("timeline segments:")
    for segment in segments:
        print(
            f"- {float(segment['start']):.1f} -> {float(segment['end']):.1f} "
            f"{segment['state']}"
        )

    print("keep intervals:")
    for interval in keep_intervals:
        print(
            f"- {float(interval.start):.1f} -> {float(interval.end):.1f} "
            f"({interval.reason})"
        )
    print(f"instruction path: {instruction_path}")

    # Assertions required by Part 4 task.
    assert Path(predictions_path).exists(), "Predictions CSV was not created."
    assert Path(timeline_path).exists(), "Timeline JSON was not created."
    assert Path(instruction_path).exists(), "Instruction JSON was not created."
    assert keep_intervals, "Expected non-empty keep_intervals."

    first_start = float(keep_intervals[0].start)
    assert 1.9 <= first_start <= 2.6, (
        "First keep interval start is unexpected; "
        f"expected around 2.0-2.5, got {first_start}."
    )
    assert len(keep_intervals) == 2, (
        f"Expected 2 rally keep intervals, found {len(keep_intervals)}."
    )

    # merge_intervals utility behavior check.
    close_intervals = [
        KeepInterval(start=1.0, end=2.0, reason="a"),
        KeepInterval(start=2.4, end=3.0, reason="b"),
    ]
    merged = merge_intervals(close_intervals, merge_gap_seconds=0.5)
    assert len(merged) == 1, "Expected merge_intervals to merge close intervals."


if __name__ == "__main__":
    main()
