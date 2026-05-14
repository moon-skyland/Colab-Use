"""State timeline builder with smoothing and CSV->JSON utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from model.common.schemas import StatePrediction, StateSegment


class TimelineBuilder:
    """Builds a clean state timeline from window-level predictions."""

    def build(self, predictions: list[StatePrediction]) -> list[StateSegment]:
        """Merge consecutive same-state predictions into state segments."""
        if not predictions:
            return []

        ordered = sorted(predictions, key=lambda item: (item.start, item.end))
        return self._merge_predictions(ordered)

    def smooth_short_segments(
        self,
        segments: list[StateSegment],
        min_duration_seconds: float = 1.0,
    ) -> list[StateSegment]:
        """Merge short middle segments when surrounded by same state."""
        if min_duration_seconds <= 0:
            return segments
        if len(segments) < 3:
            return segments

        smoothed = segments.copy()
        changed = True
        while changed and len(smoothed) >= 3:
            changed = False
            for idx in range(1, len(smoothed) - 1):
                prev_seg = smoothed[idx - 1]
                curr_seg = smoothed[idx]
                next_seg = smoothed[idx + 1]
                duration = curr_seg.end - curr_seg.start

                if duration >= min_duration_seconds:
                    continue
                if prev_seg.state != next_seg.state:
                    continue

                merged_confidences = [
                    value
                    for value in (prev_seg.confidence, curr_seg.confidence, next_seg.confidence)
                    if value is not None
                ]
                merged_confidence = (
                    float(sum(merged_confidences) / len(merged_confidences))
                    if merged_confidences
                    else None
                )

                merged = StateSegment(
                    start=prev_seg.start,
                    end=next_seg.end,
                    state=prev_seg.state,
                    confidence=merged_confidence,
                )
                smoothed = smoothed[: idx - 1] + [merged] + smoothed[idx + 2 :]
                changed = True
                break

        return smoothed

    def build_and_smooth(
        self,
        predictions: list[StatePrediction],
        min_duration_seconds: float = 1.0,
    ) -> list[StateSegment]:
        """Build merged timeline and smooth short noisy segments."""
        raw_segments = self.build(predictions)
        return self.smooth_short_segments(raw_segments, min_duration_seconds)

    def build_from_predictions_csv(
        self,
        predictions_csv_path: str,
        output_json_path: str = "backend/outputs/state_timeline.json",
        min_duration_seconds: float = 1.0,
    ) -> str:
        """Read prediction CSV, build+smooth timeline, and save JSON."""
        path = Path(predictions_csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Predictions CSV not found: {predictions_csv_path}")

        frame = pd.read_csv(path)
        required_columns = {"video", "start", "end", "predicted_state", "confidence"}
        missing = sorted(required_columns - set(frame.columns))
        if missing:
            raise ValueError(
                "Predictions CSV missing required columns: " + ", ".join(missing)
            )

        predictions = [
            StatePrediction(
                start=float(record["start"]),
                end=float(record["end"]),
                state=str(record["predicted_state"]),
                confidence=(
                    float(record["confidence"])
                    if pd.notna(record["confidence"])
                    else None
                ),
            )
            for record in frame.to_dict(orient="records")
        ]

        timeline = self.build_and_smooth(
            predictions=predictions,
            min_duration_seconds=min_duration_seconds,
        )
        output_path = Path(output_json_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "state": segment.state,
                    "confidence": segment.confidence,
                }
                for segment in timeline
            ]
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(output_path)

    def save_timeline_json(
        self,
        timeline: list[StateSegment],
        output_json_path: str = "backend/outputs/state_timeline.json",
    ) -> str:
        """Save timeline segments to standardized JSON file."""
        output_path = Path(output_json_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "state": segment.state,
                    "confidence": segment.confidence,
                }
                for segment in timeline
            ]
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(output_path)

    def _merge_predictions(
        self, predictions: list[StatePrediction]
    ) -> list[StateSegment]:
        """Merge consecutive same-state predictions and average confidence."""
        segments: list[StateSegment] = []
        current = predictions[0]
        running_confidence: list[float] = []
        if current.confidence is not None:
            running_confidence.append(current.confidence)

        for prediction in predictions[1:]:
            if prediction.state == current.state:
                current = StatePrediction(
                    start=current.start,
                    end=prediction.end,
                    state=current.state,
                    confidence=current.confidence,
                )
                if prediction.confidence is not None:
                    running_confidence.append(prediction.confidence)
                continue

            segment_confidence = (
                float(sum(running_confidence) / len(running_confidence))
                if running_confidence
                else None
            )
            segments.append(
                StateSegment(
                    start=current.start,
                    end=current.end,
                    state=current.state,
                    confidence=segment_confidence,
                )
            )
            current = prediction
            running_confidence = []
            if current.confidence is not None:
                running_confidence.append(current.confidence)

        segment_confidence = (
            float(sum(running_confidence) / len(running_confidence))
            if running_confidence
            else None
        )
        segments.append(
            StateSegment(
                start=current.start,
                end=current.end,
                state=current.state,
                confidence=segment_confidence,
            )
        )
        return segments

    # Backward compatibility aliases used by earlier demo scripts.
    def build_from_csv(
        self,
        predictions_csv_path: str,
        state_column: str = "predicted_state",
    ) -> list[StateSegment]:
        path = Path(predictions_csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Predictions CSV not found: {predictions_csv_path}")
        frame = pd.read_csv(path)
        required_columns = {"start", "end", state_column}
        missing = sorted(required_columns - set(frame.columns))
        if missing:
            raise ValueError(
                "Predictions CSV missing required columns: " + ", ".join(missing)
            )
        predictions = [
            StatePrediction(
                start=float(record["start"]),
                end=float(record["end"]),
                state=str(record[state_column]),
                confidence=(
                    float(record["confidence"])
                    if "confidence" in frame.columns and pd.notna(record["confidence"])
                    else None
                ),
            )
            for record in frame.to_dict(orient="records")
        ]
        return self.build_and_smooth(predictions=predictions, min_duration_seconds=1.0)
