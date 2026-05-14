"""Attach manual state labels to feature CSV windows."""

import json
from pathlib import Path

import pandas as pd

from model.features.feature_io import FEATURE_COLUMNS


def attach_manual_state_labels(
    features_inference_csv_path: str,
    labels_json_path: str,
    output_train_csv_path: str,
) -> str:
    """Attach manual labels to inference features and save training CSV.

    Label JSON format:
    {
      "labels": [
        {"start": 0.0, "end": 2.0, "state": "READY_TO_SERVE"},
        {"start": 2.0, "end": 6.0, "state": "RALLY_ACTIVE"}
      ]
    }
    """
    inference_path = Path(features_inference_csv_path)
    labels_path = Path(labels_json_path)
    output_path = Path(output_train_csv_path)

    if not inference_path.exists():
        raise FileNotFoundError(f"Inference features CSV not found: {features_inference_csv_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Manual labels JSON not found: {labels_json_path}")

    frame = pd.read_csv(inference_path)
    missing_columns = sorted(set(FEATURE_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(
            "Inference feature CSV missing required columns: "
            + ", ".join(missing_columns)
        )

    with open(labels_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    labels = payload.get("labels", [])
    if not isinstance(labels, list):
        raise ValueError("labels JSON must contain a list at key 'labels'.")

    states: list[str | None] = []
    for row in frame.itertuples(index=False):
        row_state = _find_state_for_window(start=float(row.start), end=float(row.end), labels=labels)
        states.append(row_state)

    frame["state"] = states
    labeled_frame = frame.dropna(subset=["state"]).copy()
    if labeled_frame.empty:
        raise ValueError(
            "No windows overlapped with manual labels. Check label ranges against feature times."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    labeled_frame.to_csv(output_path, index=False)
    return str(output_path)


def _find_state_for_window(
    start: float, end: float, labels: list[dict[str, object]]
) -> str | None:
    midpoint = (start + end) / 2.0
    for label in labels:
        label_start = float(label.get("start", -1.0))
        label_end = float(label.get("end", -1.0))
        state = label.get("state")
        if isinstance(state, str) and label_start <= midpoint < label_end:
            return state
    return None
