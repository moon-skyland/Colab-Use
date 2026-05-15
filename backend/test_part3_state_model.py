"""Part 3 state model demo with synthetic feature data."""

from pathlib import Path

import pandas as pd

from model.segmentation.state_predictor import StatePredictor
from model.training.train_state_model import train_state_model

TRAIN_CSV_PATH = "data/features/demo_features_train.csv"
MODEL_PATH = "backend/models/demo_state_model.pkl"
INFERENCE_CSV_PATH = "data/features/demo_features_inference.csv"
PREDICTIONS_CSV_PATH = "backend/outputs/demo_state_predictions.csv"


def _build_synthetic_training_frame() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    states = ["DEAD_TIME", "READY_TO_SERVE", "RALLY_ACTIVE", "RALLY_ENDING"]

    for idx in range(32):
        state = states[idx % len(states)]
        if state == "DEAD_TIME":
            ball_visible_ratio = 0.15
            ball_mean_speed = 1.2
            player_mean_speed = 0.3
        elif state == "READY_TO_SERVE":
            ball_visible_ratio = 0.65
            ball_mean_speed = 2.0
            player_mean_speed = 0.8
        elif state == "RALLY_ACTIVE":
            ball_visible_ratio = 0.95
            ball_mean_speed = 14.5
            player_mean_speed = 2.9
        else:  # RALLY_ENDING
            ball_visible_ratio = 0.75
            ball_mean_speed = 7.5
            player_mean_speed = 1.7

        start = float(idx)
        end = float(idx + 1)
        rows.append(
            {
                "video": "demo_video.mp4",
                "start": start,
                "end": end,
                "ball_visible_ratio": ball_visible_ratio,
                "ball_mean_speed": ball_mean_speed,
                "ball_max_speed": ball_mean_speed + 1.5,
                "ball_missing_gap": 0 if ball_visible_ratio > 0.5 else 3,
                "player_mean_speed": player_mean_speed,
                "player_max_speed": player_mean_speed + 1.2,
                "players_in_service_zone": 2 if state == "READY_TO_SERVE" else 1,
                "players_movement_score": min(player_mean_speed / 5.0, 1.0),
                "state": state,
            }
        )
    return pd.DataFrame(rows)


def _build_synthetic_inference_frame() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for idx in range(12):
        start = float(idx)
        end = float(idx + 1)
        rally_bias = 1.0 if idx % 3 == 0 else 0.0
        rows.append(
            {
                "video": "demo_video.mp4",
                "start": start,
                "end": end,
                "ball_visible_ratio": 0.6 + (0.3 * rally_bias),
                "ball_mean_speed": 3.0 + (10.0 * rally_bias),
                "ball_max_speed": 4.0 + (11.0 * rally_bias),
                "ball_missing_gap": 0 if rally_bias else 2,
                "player_mean_speed": 0.9 + (1.8 * rally_bias),
                "player_max_speed": 1.4 + (2.4 * rally_bias),
                "players_in_service_zone": 2 if idx % 4 == 0 else 1,
                "players_movement_score": min((0.9 + (1.8 * rally_bias)) / 5.0, 1.0),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    Path("data/features").mkdir(parents=True, exist_ok=True)
    Path("backend/models").mkdir(parents=True, exist_ok=True)
    Path("backend/outputs").mkdir(parents=True, exist_ok=True)

    train_frame = _build_synthetic_training_frame()
    train_frame.to_csv(TRAIN_CSV_PATH, index=False)

    saved_model = train_state_model(
        features_csv_path=TRAIN_CSV_PATH,
        output_model_path=MODEL_PATH,
    )

    inference_frame = _build_synthetic_inference_frame()
    inference_frame.to_csv(INFERENCE_CSV_PATH, index=False)

    predictor = StatePredictor(
        model_path=MODEL_PATH,
        metadata_path="backend/models/state_model_metadata.json",
        mock_if_missing=False,
    )
    predictions_path = predictor.predict_csv(
        features_csv_path=INFERENCE_CSV_PATH,
        output_csv_path=PREDICTIONS_CSV_PATH,
    )

    predictions_preview = pd.read_csv(predictions_path).head()

    print(f"training file path: {TRAIN_CSV_PATH}")
    print(f"model path: {saved_model}")
    print(f"predictions file path: {predictions_path}")
    print("first few predictions:")
    print(predictions_preview[["video", "start", "end", "predicted_state", "confidence"]])


if __name__ == "__main__":
    main()
