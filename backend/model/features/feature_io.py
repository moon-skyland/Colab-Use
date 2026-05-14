"""CSV utilities for feature rows."""

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from model.common.schemas import FeatureRow, LabeledFeatureRow

FEATURE_COLUMNS = [
    "video",
    "start",
    "end",
    "ball_visible_ratio",
    "ball_mean_speed",
    "ball_max_speed",
    "ball_missing_gap",
    "player_mean_speed",
    "player_max_speed",
    "players_in_service_zone",
    "players_movement_score",
]


def save_feature_rows_csv(feature_rows: list[FeatureRow], output_csv_path: str) -> str:
    """Save inference feature rows to CSV."""
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([asdict(row) for row in feature_rows], columns=FEATURE_COLUMNS)
    frame.to_csv(output_path, index=False)
    return str(output_path)


def save_labeled_feature_rows_csv(
    feature_rows: list[LabeledFeatureRow], output_csv_path: str
) -> str:
    """Save labeled training feature rows to CSV."""
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        [asdict(row) for row in feature_rows], columns=FEATURE_COLUMNS + ["state"]
    )
    frame.to_csv(output_path, index=False)
    return str(output_path)


def load_feature_rows_csv(input_csv_path: str) -> list[FeatureRow]:
    """Load inference feature rows from CSV."""
    path = Path(input_csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature CSV not found: {input_csv_path}")
    frame = pd.read_csv(path)
    _validate_columns(frame.columns.tolist(), FEATURE_COLUMNS, input_csv_path)
    return [FeatureRow(**record) for record in frame.to_dict(orient="records")]


def _validate_columns(columns: list[str], required: list[str], csv_path: str) -> None:
    missing = sorted(set(required) - set(columns))
    if missing:
        raise ValueError(
            f"CSV '{csv_path}' is missing required columns: {', '.join(missing)}"
        )
