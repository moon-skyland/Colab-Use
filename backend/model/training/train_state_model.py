"""Train a RandomForest state classifier from labeled feature CSV."""

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

REQUIRED_FEATURE_COLUMNS = [
    "ball_visible_ratio",
    "ball_mean_speed",
    "ball_max_speed",
    "ball_missing_gap",
    "player_mean_speed",
    "player_max_speed",
    "players_in_service_zone",
    "players_movement_score",
]
LABEL_COLUMN = "state"


def train_state_model(
    features_csv_path: str = "data/features/features_train.csv",
    output_model_path: str = "backend/models/state_model.pkl",
) -> str:
    """Train and persist a state model and metadata."""
    csv_path = Path(features_csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Training features CSV not found: {features_csv_path}")

    frame = pd.read_csv(csv_path)
    required_columns = set(REQUIRED_FEATURE_COLUMNS + [LABEL_COLUMN])
    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise ValueError(
            "Training CSV is missing required columns: " + ", ".join(missing_columns)
        )

    clean_frame = frame.dropna(subset=REQUIRED_FEATURE_COLUMNS + [LABEL_COLUMN]).copy()
    if len(clean_frame) < 10:
        raise ValueError(
            f"Need at least 10 valid training rows after cleanup, found {len(clean_frame)}."
        )

    y = clean_frame[LABEL_COLUMN].astype(str)
    if y.nunique() < 2:
        raise ValueError("Need at least 2 unique state classes for training.")

    X = clean_frame[REQUIRED_FEATURE_COLUMNS]
    class_counts = y.value_counts()
    num_classes = int(y.nunique())
    expected_valid_rows = int(len(clean_frame) * 0.2)
    can_stratify = bool(
        class_counts.min() >= 2 and expected_valid_rows >= num_classes
    )

    split_kwargs: dict[str, object] = {
        "test_size": 0.2,
        "random_state": 42,
    }
    if can_stratify:
        split_kwargs["stratify"] = y
    else:
        print(
            "Warning: not enough rows per class for stratified split; "
            "using non-stratified train/validation split."
        )

    X_train, X_valid, y_train, y_valid = train_test_split(X, y, **split_kwargs)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_valid)
    accuracy = float(accuracy_score(y_valid, y_pred))
    print(f"Validation accuracy: {accuracy:.4f}")
    print("Classification report:")
    print(classification_report(y_valid, y_pred, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(y_valid, y_pred))

    output_path = Path(output_model_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)

    metadata_path = output_path.with_name("state_model_metadata.json")
    metadata = {
        "feature_columns": REQUIRED_FEATURE_COLUMNS,
        "label_column": LABEL_COLUMN,
        "classes": sorted(y.unique().tolist()),
        "training_rows": int(len(clean_frame)),
        "validation_accuracy": accuracy,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved model to: {output_path}")
    print(f"Saved metadata to: {metadata_path}")
    return str(output_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train badminton state model.")
    parser.add_argument(
        "--features",
        default="data/features/features_train.csv",
        help="Path to labeled training features CSV.",
    )
    parser.add_argument(
        "--output",
        default="backend/models/state_model.pkl",
        help="Path to output model .pkl file.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    train_state_model(features_csv_path=args.features, output_model_path=args.output)
