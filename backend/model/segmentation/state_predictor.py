"""State prediction using trained state model artifact."""

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from model.common.schemas import FeatureRow, StatePrediction

DEFAULT_FEATURE_COLUMNS = [
    "ball_visible_ratio",
    "ball_mean_speed",
    "ball_max_speed",
    "ball_missing_gap",
    "player_mean_speed",
    "player_max_speed",
    "players_in_service_zone",
    "players_movement_score",
]


class StatePredictor:
    """Loads a trained state model and predicts window-level states."""

    def __init__(
        self,
        model_path: str = "backend/models/state_model.pkl",
        metadata_path: str = "backend/models/state_model_metadata.json",
        mock_if_missing: bool = True,
    ) -> None:
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.mock_if_missing = mock_if_missing
        self.mock_mode = False

        self.model: Any | None = None
        self.label_encoder: Any | None = None
        self.feature_columns: list[str] = DEFAULT_FEATURE_COLUMNS.copy()

        self._load_model()

    def predict(self, feature_rows: list[FeatureRow]) -> list[StatePrediction]:
        """Predict states for in-memory feature rows."""
        if not feature_rows:
            return []

        if self.mock_mode:
            return [
                StatePrediction(
                    start=row.start,
                    end=row.end,
                    state="DEAD_TIME",
                    confidence=0.0,
                )
                for row in feature_rows
            ]

        if self.model is None:
            raise RuntimeError("State model is not available for prediction.")

        frame = pd.DataFrame([asdict(row) for row in feature_rows])
        missing_columns = sorted(set(self.feature_columns) - set(frame.columns))
        if missing_columns:
            raise ValueError(
                "Feature rows are missing required columns for prediction: "
                + ", ".join(missing_columns)
            )

        X = frame[self.feature_columns]
        raw_predictions = self.model.predict(X)
        if self.label_encoder is not None:
            predicted_states = self.label_encoder.inverse_transform(raw_predictions)
        else:
            predicted_states = raw_predictions

        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(X)
            confidences: list[float | None] = [float(row.max()) for row in probabilities]
        else:
            confidences = [None] * len(feature_rows)

        return [
            StatePrediction(
                start=row.start,
                end=row.end,
                state=str(state),
                confidence=conf,
            )
            for row, state, conf in zip(feature_rows, predicted_states, confidences)
        ]

    def predict_csv(
        self,
        features_csv_path: str,
        output_csv_path: str = "backend/outputs/state_predictions.csv",
    ) -> str:
        """Predict states from a features CSV and write prediction CSV."""
        path = Path(features_csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Features CSV not found: {features_csv_path}")

        frame = pd.read_csv(path)
        required_base_columns = {"video", "start", "end"}
        missing_base = sorted(required_base_columns - set(frame.columns))
        if missing_base:
            raise ValueError(
                "Features CSV missing required metadata columns: "
                + ", ".join(missing_base)
            )

        if self.mock_mode:
            predicted_states = ["DEAD_TIME"] * len(frame)
            confidences: list[float | None] = [0.0] * len(frame)
        else:
            missing_features = sorted(set(self.feature_columns) - set(frame.columns))
            if missing_features:
                raise ValueError(
                    "Features CSV missing required model feature columns: "
                    + ", ".join(missing_features)
                )
            X = frame[self.feature_columns]
            raw_predictions = self.model.predict(X)
            if self.label_encoder is not None:
                predicted_states = self.label_encoder.inverse_transform(raw_predictions)
            else:
                predicted_states = raw_predictions

            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(X)
                confidences = [float(row.max()) for row in probs]
            else:
                confidences = [None] * len(frame)

        output_frame = frame.copy()
        output_frame["predicted_state"] = [str(value) for value in predicted_states]
        output_frame["confidence"] = confidences

        output_path = Path(output_csv_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_frame.to_csv(output_path, index=False)
        return str(output_path)

    def _load_model(self) -> None:
        model_path = Path(self.model_path)
        metadata_path = Path(self.metadata_path)

        if not model_path.exists():
            if self.mock_if_missing:
                self.mock_mode = True
                return
            raise FileNotFoundError(
                f"State model file not found: {self.model_path}. Train model before prediction."
            )

        loaded = joblib.load(model_path)
        if isinstance(loaded, dict) and "model" in loaded:
            self.model = loaded["model"]
            self.label_encoder = loaded.get("label_encoder")
            feature_columns = loaded.get("feature_columns")
            if isinstance(feature_columns, list) and feature_columns:
                self.feature_columns = [str(column) for column in feature_columns]
            return

        self.model = loaded
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            feature_columns = metadata.get("feature_columns")
            if isinstance(feature_columns, list) and feature_columns:
                self.feature_columns = [str(column) for column in feature_columns]

    # Backward-compat alias for previous API
    def predict_from_csv(self, features_csv_path: str, output_csv_path: str) -> str:
        return self.predict_csv(features_csv_path, output_csv_path)
