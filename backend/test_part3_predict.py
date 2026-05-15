"""Part 3 prediction-only demo using existing CSV/model artifacts."""

from pathlib import Path

from model.segmentation.state_predictor import StatePredictor


FEATURES_INFERENCE_CSV = "data/features/features_inference.csv"
MODEL_PATH = "backend/models/state_model.pkl"
OUTPUT_PREDICTIONS_CSV = "data/features/state_predictions.csv"


def main() -> None:
    features_path = Path(FEATURES_INFERENCE_CSV)
    model_path = Path(MODEL_PATH)
    if not features_path.exists():
        print(f"Inference features CSV not found: {FEATURES_INFERENCE_CSV}")
        return
    if not model_path.exists():
        print(f"State model not found: {MODEL_PATH}")
        return

    predictor = StatePredictor(model_path=str(model_path))
    output_path = predictor.predict_from_csv(
        features_csv_path=str(features_path),
        output_csv_path=OUTPUT_PREDICTIONS_CSV,
    )
    print(f"Saved predictions to: {output_path}")


if __name__ == "__main__":
    main()
