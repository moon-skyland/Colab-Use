"""Utilities for loading, saving, validating, and merging edit instructions."""

from __future__ import annotations

import json
from pathlib import Path

from model.common.schemas import EditInstruction, KeepInterval


def load_edit_instruction(json_path: str) -> EditInstruction:
    """Load edit instruction JSON into EditInstruction schema."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Edit instruction JSON not found: {json_path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    keep_payload = payload.get("keep_intervals", [])
    if not isinstance(keep_payload, list):
        raise ValueError("Edit instruction JSON must contain a list at 'keep_intervals'.")

    instruction = EditInstruction(
        video_path=str(payload.get("video_path", "")),
        output_path=str(payload.get("output_path", "")),
        keep_intervals=[
            KeepInterval(
                start=float(item["start"]),
                end=float(item["end"]),
                reason=(str(item["reason"]) if item.get("reason") is not None else None),
            )
            for item in keep_payload
        ],
        version=str(payload.get("version", "1.0")),
        settings=payload.get("settings"),
    )
    validate_edit_instruction(instruction)
    return instruction


def save_edit_instruction(
    instruction: EditInstruction,
    json_path: str,
    settings: dict | None = None,
) -> str:
    """Save EditInstruction to JSON, optionally including settings metadata."""
    validate_edit_instruction(instruction)

    output_path = Path(json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "version": instruction.version if instruction.version else "1.0",
        "video_path": instruction.video_path,
        "output_path": instruction.output_path,
        "keep_intervals": [
            {"start": item.start, "end": item.end, "reason": item.reason}
            for item in instruction.keep_intervals
        ],
    }
    final_settings = settings if settings is not None else instruction.settings
    if final_settings is not None:
        payload["settings"] = final_settings

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output_path)


def validate_edit_instruction(instruction: EditInstruction) -> None:
    """Validate basic structural and interval rules for edit instruction."""
    if not instruction.video_path or not instruction.video_path.strip():
        raise ValueError("EditInstruction.video_path must not be empty.")
    if not instruction.output_path or not instruction.output_path.strip():
        raise ValueError("EditInstruction.output_path must not be empty.")

    intervals = instruction.keep_intervals
    for idx, interval in enumerate(intervals):
        if interval.start >= interval.end:
            raise ValueError(
                f"Invalid keep interval at index {idx}: start must be < end "
                f"(got {interval.start} >= {interval.end})."
            )

    for idx in range(1, len(intervals)):
        prev_interval = intervals[idx - 1]
        curr_interval = intervals[idx]
        if curr_interval.start < prev_interval.start:
            raise ValueError("Keep intervals must be sorted by start time.")
        if curr_interval.start < prev_interval.end:
            raise ValueError(
                f"Keep intervals overlap between indices {idx-1} and {idx}: "
                f"[{prev_interval.start}, {prev_interval.end}] and "
                f"[{curr_interval.start}, {curr_interval.end}]."
            )


def merge_intervals(
    intervals: list[KeepInterval],
    merge_gap_seconds: float = 0.5,
) -> list[KeepInterval]:
    """Sort and merge intervals when gap <= merge_gap_seconds."""
    if not intervals:
        return []
    if merge_gap_seconds < 0:
        raise ValueError("merge_gap_seconds must be >= 0.")

    ordered = sorted(intervals, key=lambda item: (item.start, item.end))
    merged: list[KeepInterval] = [ordered[0]]

    for interval in ordered[1:]:
        current = merged[-1]
        gap = interval.start - current.end
        if gap <= merge_gap_seconds:
            current.end = max(current.end, interval.end)
            if current.reason != interval.reason:
                reasons = [reason for reason in [current.reason, interval.reason] if reason]
                current.reason = "+".join(dict.fromkeys(reasons)) if reasons else "merged_interval"
        else:
            merged.append(
                KeepInterval(
                    start=interval.start,
                    end=interval.end,
                    reason=interval.reason,
                )
            )
    return merged
