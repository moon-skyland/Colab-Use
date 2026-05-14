"""Attach manual state intervals to extracted feature windows."""

import json
from pathlib import Path
from typing import Any

from model.common.schemas import FeatureRow, LabeledFeatureRow


class StateLabeler:
    """Maps feature windows to manual state intervals."""

    ALLOWED_STATES = {
        "DEAD_TIME",
        "READY_TO_SERVE",
        "RALLY_ACTIVE",
        "RALLY_ENDING",
    }

    def load_state_labels(self, label_json_path: str) -> dict[str, Any]:
        """Load and validate state label JSON payload."""
        path = Path(label_json_path)
        if not path.exists():
            raise FileNotFoundError(f"State label JSON not found: {label_json_path}")

        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        state_intervals = payload.get("state_intervals")
        if not isinstance(state_intervals, list):
            raise ValueError(
                "State label JSON must include a list field 'state_intervals'."
            )

        for idx, interval in enumerate(state_intervals):
            if not isinstance(interval, dict):
                raise ValueError(f"state_intervals[{idx}] must be an object.")

            missing = {"start", "end", "state"} - set(interval.keys())
            if missing:
                raise ValueError(
                    f"state_intervals[{idx}] missing keys: {', '.join(sorted(missing))}"
                )

            start = float(interval["start"])
            end = float(interval["end"])
            state = str(interval["state"])
            if end <= start:
                raise ValueError(
                    f"state_intervals[{idx}] must have end > start (got {start} to {end})."
                )
            if state not in self.ALLOWED_STATES:
                raise ValueError(
                    f"state_intervals[{idx}] has invalid state '{state}'. "
                    f"Allowed: {', '.join(sorted(self.ALLOWED_STATES))}"
                )

        return payload

    def find_state_for_window(
        self, start: float, end: float, state_intervals: list[dict[str, Any]]
    ) -> str:
        """Return state with largest overlap against [start, end)."""
        if end <= start:
            raise ValueError(f"Window end must be greater than start (got {start} to {end}).")

        best_state = "UNKNOWN"
        best_overlap = 0.0

        for interval in state_intervals:
            overlap_start = max(start, float(interval["start"]))
            overlap_end = min(end, float(interval["end"]))
            overlap = max(0.0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_state = str(interval["state"])

        return best_state if best_overlap > 0.0 else "UNKNOWN"

    def attach_labels(
        self,
        feature_rows: list[FeatureRow],
        label_json_path: str,
        skip_unknown: bool = True,
    ) -> list[LabeledFeatureRow]:
        """Attach manual labels to feature rows based on max overlap."""
        payload = self.load_state_labels(label_json_path)
        state_intervals = payload["state_intervals"]

        labeled_rows: list[LabeledFeatureRow] = []
        for row in feature_rows:
            state = self.find_state_for_window(row.start, row.end, state_intervals)
            if state == "UNKNOWN":
                if skip_unknown:
                    continue
                raise ValueError(
                    f"Could not assign state for window {row.start:.3f}-{row.end:.3f}."
                )

            labeled_rows.append(
                LabeledFeatureRow(
                    video=row.video,
                    start=row.start,
                    end=row.end,
                    ball_visible_ratio=row.ball_visible_ratio,
                    ball_mean_speed=row.ball_mean_speed,
                    ball_max_speed=row.ball_max_speed,
                    ball_missing_gap=row.ball_missing_gap,
                    player_mean_speed=row.player_mean_speed,
                    player_max_speed=row.player_max_speed,
                    players_in_service_zone=row.players_in_service_zone,
                    players_movement_score=row.players_movement_score,
                    state=state,
                )
            )
        return labeled_rows
