"""CSV read/write helpers for feature rows."""

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

LABELED_FEATURE_COLUMNS = FEATURE_COLUMNS + ["state"]


def write_feature_rows(rows: list[FeatureRow], output_csv_path: str) -> str:
    """Write inference feature rows (without state) to CSV."""
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([asdict(row) for row in rows], columns=FEATURE_COLUMNS)
    frame.to_csv(output_path, index=False)
    return str(output_path)


def write_labeled_feature_rows(
    rows: list[LabeledFeatureRow], output_csv_path: str
) -> str:
    """Write labeled training feature rows (with state) to CSV."""
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([asdict(row) for row in rows], columns=LABELED_FEATURE_COLUMNS)
    frame.to_csv(output_path, index=False)
    return str(output_path)


def read_feature_rows(csv_path: str) -> list[FeatureRow]:
    """Read inference feature rows from CSV."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature CSV not found: {csv_path}")
    frame = pd.read_csv(path)
    _validate_required_columns(frame.columns.tolist(), FEATURE_COLUMNS, csv_path)
    return [FeatureRow(**record) for record in frame[FEATURE_COLUMNS].to_dict(orient="records")]


def read_labeled_feature_rows(csv_path: str) -> list[LabeledFeatureRow]:
    """Read labeled training feature rows from CSV."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Labeled feature CSV not found: {csv_path}")
    frame = pd.read_csv(path)
    _validate_required_columns(frame.columns.tolist(), LABELED_FEATURE_COLUMNS, csv_path)
    return [
        LabeledFeatureRow(**record)
        for record in frame[LABELED_FEATURE_COLUMNS].to_dict(orient="records")
    ]


def _validate_required_columns(
    actual_columns: list[str], required_columns: list[str], csv_path: str
) -> None:
    missing_columns = sorted(set(required_columns) - set(actual_columns))
    if missing_columns:
        raise ValueError(
            f"CSV '{csv_path}' is missing required columns: {', '.join(missing_columns)}"
        )
