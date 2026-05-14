"""Part 3 end-to-end demo for feature -> train -> predict pipeline."""

import json
from pathlib import Path

from model.common.schemas import AthleteCourtPosition, ShuttlecockCourtPosition
from model.features.feature_extractor import FeatureExtractor
from model.features.feature_io import save_feature_rows_csv
from model.segmentation.state_predictor import StatePredictor
from model.training.manual_label_attachment import attach_manual_state_labels
from model.training.train_state_model import train_state_model


def _build_demo_positions(num_frames: int = 360) -> tuple[list[AthleteCourtPosition], list[ShuttlecockCourtPosition]]:
    athlete_positions: list[AthleteCourtPosition] = []
    shuttle_positions: list[ShuttlecockCourtPosition] = []

    for frame_index in range(num_frames):
        t = frame_index / 30.0
        if t < 4.0:
            phase = "READY_TO_SERVE"
        elif t < 8.0:
            phase = "RALLY_ACTIVE"
        else:
            phase = "DEAD_TIME"

        # Two athletes with simple motion profiles.
        for track_id in (1, 2):
            moving_scale = 0.15 if phase == "READY_TO_SERVE" else (1.25 if phase == "RALLY_ACTIVE" else 0.08)
            x_base = 1.5 if track_id == 1 else 4.6
            y_base = 10.5 if track_id == 1 else 2.8
            x = x_base + moving_scale * ((frame_index % 30) / 30.0)
            y = y_base + moving_scale * ((frame_index % 20) / 20.0)
            service_zone = (track_id == 1 and y > 6.7) or (track_id == 2 and y <= 6.7)
            athlete_positions.append(
                AthleteCourtPosition(
                    frame_index=frame_index,
                    track_id=track_id,
                    feet_court=(x, y),
                    zone="near_left_service" if track_id == 1 else "far_right_service",
                    in_service_zone=service_zone,
                    speed_meters_per_second=moving_scale * 2.0,
                )
            )

        # Shuttlecock visibility and speed by phase.
        if phase == "READY_TO_SERVE":
            visible = True
            speed = 2.0
            missing_count = 0
        elif phase == "RALLY_ACTIVE":
            visible = True
            speed = 14.0
            missing_count = 0
        else:
            visible = frame_index % 15 == 0
            speed = 1.0 if visible else None
            missing_count = 0 if visible else min(10, frame_index % 15)

        ball = (3.05 + 1.8 * ((frame_index % 50) / 50.0), 6.7) if visible else None
        shuttle_positions.append(
            ShuttlecockCourtPosition(
                frame_index=frame_index,
                visible=visible,
                ball_court=ball,
                inside_court=True if visible else None,
                speed_meters_per_second=speed,
                missing_count=missing_count,
            )
        )

    return athlete_positions, shuttle_positions


def main() -> None:
    features_dir = Path("backend/data/features")
    labels_dir = Path("backend/data/state_labels")
    models_dir = Path("backend/models")
    features_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    inference_csv = features_dir / "features_inference.csv"
    train_csv = features_dir / "features_train.csv"
    labels_json = labels_dir / "manual_labels.json"
    model_path = models_dir / "state_model.pkl"
    predictions_csv = features_dir / "state_predictions.csv"

    athlete_positions, shuttle_positions = _build_demo_positions()
    extractor = FeatureExtractor()
    feature_rows = extractor.extract_features_over_time(
        video_name="sample_demo.mp4",
        athlete_positions=athlete_positions,
        shuttlecock_positions=shuttle_positions,
        fps=30.0,
        window_seconds=1.0,
    )
    save_feature_rows_csv(feature_rows, str(inference_csv))

    # Simulate manual labeling artifact used for training set generation.
    labels_payload = {
        "labels": [
            {"start": 0.0, "end": 4.0, "state": "READY_TO_SERVE"},
            {"start": 4.0, "end": 8.0, "state": "RALLY_ACTIVE"},
            {"start": 8.0, "end": 12.0, "state": "DEAD_TIME"},
        ]
    }
    labels_json.write_text(json.dumps(labels_payload, indent=2), encoding="utf-8")

    attach_manual_state_labels(
        features_inference_csv_path=str(inference_csv),
        labels_json_path=str(labels_json),
        output_train_csv_path=str(train_csv),
    )
    train_state_model(features_csv_path=str(train_csv), output_model_path=str(model_path))

    predictor = StatePredictor(model_path=str(model_path))
    predictor.predict_from_csv(str(inference_csv), str(predictions_csv))

    print("Part 3 pipeline completed.")
    print(f"features_inference.csv: {inference_csv}")
    print(f"features_train.csv: {train_csv}")
    print(f"state_model.pkl: {model_path}")
    print(f"state_predictions.csv: {predictions_csv}")


if __name__ == "__main__":
    main()
