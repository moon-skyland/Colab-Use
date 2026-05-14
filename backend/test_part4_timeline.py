"""Part 4 demo: state_predictions.csv -> state_timeline.json."""

from pathlib import Path

import pandas as pd

from model.segmentation.timeline_builder import TimelineBuilder


PREDICTIONS_CSV_PATH = "backend/outputs/demo_state_predictions_part4.csv"
TIMELINE_JSON_PATH = "backend/outputs/state_timeline.json"


def _build_synthetic_predictions_csv(output_csv_path: str) -> str:
    rows = [
        {"video": "demo_video.mp4", "start": 0.0, "end": 1.0, "predicted_state": "DEAD_TIME", "confidence": 0.95},
        {"video": "demo_video.mp4", "start": 1.0, "end": 2.0, "predicted_state": "DEAD_TIME", "confidence": 0.94},
        {"video": "demo_video.mp4", "start": 2.0, "end": 3.0, "predicted_state": "READY_TO_SERVE", "confidence": 0.76},
        # Flicker noise to be smoothed:
        {"video": "demo_video.mp4", "start": 3.0, "end": 4.0, "predicted_state": "DEAD_TIME", "confidence": 0.55},
        {"video": "demo_video.mp4", "start": 4.0, "end": 5.0, "predicted_state": "READY_TO_SERVE", "confidence": 0.80},
        {"video": "demo_video.mp4", "start": 5.0, "end": 6.0, "predicted_state": "RALLY_ACTIVE", "confidence": 0.90},
        {"video": "demo_video.mp4", "start": 6.0, "end": 7.0, "predicted_state": "RALLY_ACTIVE", "confidence": 0.92},
        {"video": "demo_video.mp4", "start": 7.0, "end": 8.0, "predicted_state": "RALLY_ENDING", "confidence": 0.84},
        {"video": "demo_video.mp4", "start": 8.0, "end": 9.0, "predicted_state": "DEAD_TIME", "confidence": 0.93},
    ]
    frame = pd.DataFrame(rows)
    out = Path(output_csv_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    return str(out)


def main() -> None:
    predictions_csv = _build_synthetic_predictions_csv(PREDICTIONS_CSV_PATH)

    builder = TimelineBuilder()
    timeline = builder.build_from_csv(predictions_csv_path=predictions_csv)
    timeline_json = builder.save_timeline_json(
        timeline=timeline,
        output_json_path=TIMELINE_JSON_PATH,
    )

    print(f"predictions csv: {predictions_csv}")
    print(f"timeline json: {timeline_json}")
    print("timeline segments:")
    for segment in timeline:
        print(
            f"- {segment.start:.1f} -> {segment.end:.1f} | "
            f"{segment.state} | conf={segment.confidence}"
        )


if __name__ == "__main__":
    main()
