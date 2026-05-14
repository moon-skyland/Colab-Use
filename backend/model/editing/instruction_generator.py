"""Edit instruction generation from state timeline."""

from __future__ import annotations

import json
from pathlib import Path

from model.common.schemas import EditInstruction, KeepInterval, StateSegment
from model.editing.instruction_utils import (
    merge_intervals,
    save_edit_instruction,
    validate_edit_instruction,
)


class InstructionGenerator:
    """Generates EditInstruction objects from state timelines."""

    RALLY_STATE = "RALLY_ACTIVE"

    def generate(
        self,
        video_path: str,
        output_path: str,
        timeline: list[StateSegment],
        pre_roll_seconds: float = 1.0,
        post_roll_seconds: float = 0.5,
        min_keep_duration: float = 1.0,
        merge_gap_seconds: float = 0.5,
    ) -> EditInstruction:
        """Generate keep intervals from state timeline segments."""
        if not timeline:
            print("Warning: empty timeline received; returning empty keep intervals.")
            return EditInstruction(
                video_path=video_path,
                output_path=output_path,
                keep_intervals=[],
                settings={
                    "pre_roll_seconds": pre_roll_seconds,
                    "post_roll_seconds": post_roll_seconds,
                    "min_keep_duration": min_keep_duration,
                    "merge_gap_seconds": merge_gap_seconds,
                },
            )

        if pre_roll_seconds < 0 or post_roll_seconds < 0:
            raise ValueError("pre_roll_seconds and post_roll_seconds must be >= 0.")
        if min_keep_duration < 0:
            raise ValueError("min_keep_duration must be >= 0.")
        if merge_gap_seconds < 0:
            raise ValueError("merge_gap_seconds must be >= 0.")

        provisional: list[KeepInterval] = []
        for segment in sorted(timeline, key=lambda item: (item.start, item.end)):
            if segment.state != self.RALLY_STATE:
                continue

            start = max(0.0, segment.start - pre_roll_seconds)
            end = segment.end + post_roll_seconds
            if end - start < min_keep_duration:
                continue

            provisional.append(
                KeepInterval(
                    start=start,
                    end=end,
                    reason="rally_active_with_context",
                )
            )

        keep_intervals = merge_intervals(
            intervals=provisional,
            merge_gap_seconds=merge_gap_seconds,
        )
        return EditInstruction(
            video_path=video_path,
            output_path=output_path,
            keep_intervals=keep_intervals,
            settings={
                "pre_roll_seconds": pre_roll_seconds,
                "post_roll_seconds": post_roll_seconds,
                "min_keep_duration": min_keep_duration,
                "merge_gap_seconds": merge_gap_seconds,
            },
        )

    def generate_from_timeline_json(
        self,
        timeline_json_path: str,
        video_path: str,
        output_video_path: str,
        output_instruction_path: str = "backend/outputs/edit_instruction.json",
        pre_roll_seconds: float = 1.0,
        post_roll_seconds: float = 0.5,
        min_keep_duration: float = 1.0,
        merge_gap_seconds: float = 0.5,
    ) -> str:
        """Convenience wrapper around generate + validate + save.

        Preferred pipeline entrypoint is: backend/build_instruction_from_predictions.py
        """
        path = Path(timeline_json_path)
        if not path.exists():
            raise FileNotFoundError(f"Timeline JSON not found: {timeline_json_path}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        timeline_payload = payload.get("segments")
        if timeline_payload is None:
            timeline_payload = payload.get("timeline")
        if not isinstance(timeline_payload, list):
            raise ValueError(
                "Timeline JSON must contain a list at key 'segments' (or legacy 'timeline')."
            )

        timeline = [
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
            for item in timeline_payload
        ]
        instruction = self.generate(
            video_path=video_path,
            output_path=output_video_path,
            timeline=timeline,
            pre_roll_seconds=pre_roll_seconds,
            post_roll_seconds=post_roll_seconds,
            min_keep_duration=min_keep_duration,
            merge_gap_seconds=merge_gap_seconds,
        )
        validate_edit_instruction(instruction)
        return save_edit_instruction(
            instruction=instruction,
            json_path=output_instruction_path,
            settings={
                "pre_roll_seconds": pre_roll_seconds,
                "post_roll_seconds": post_roll_seconds,
                "min_keep_duration": min_keep_duration,
                "merge_gap_seconds": merge_gap_seconds,
            },
        )
