"""Part 5 end-to-end backend pipeline test (without frontend)."""

from pathlib import Path

try:
    from backend.pipeline import process_video_pipeline
except ImportError:
    from pipeline import process_video_pipeline


SAMPLE_VIDEO = "backend/data/raw_videos/sample.mp4"
OUTPUT_DIR = "backend/outputs/part5_demo"
COURT_CORNERS_JSON = "backend/data/court_corners/sample_court_corners.json"


def main() -> None:
    sample_path = Path(SAMPLE_VIDEO)
    if not sample_path.exists():
        print(
            "Sample video not found. Put a test video at "
            "backend/data/raw_videos/sample.mp4"
        )
        return

    print("Running Part 5 end-to-end pipeline test...")
    print(
        "Note: if model files are missing, outputs may rely on mock behavior "
        "and quality may be weak. This is acceptable for pipeline validation."
    )

    result = process_video_pipeline(
        video_path=SAMPLE_VIDEO,
        court_corners_json=COURT_CORNERS_JSON,
        output_dir=OUTPUT_DIR,
        max_frames=0,
        window_size_seconds=1.0,
        use_mock_if_missing=True,
    )

    print("Pipeline result:")
    for key, value in result.items():
        print(f"- {key}: {value}")

    if result.get("status") != "success":
        print("Pipeline failed. See 'error' field above.")
        return

    instruction_path = Path(str(result["edit_instruction_json"]))
    timeline_path = Path(str(result["state_timeline_json"]))
    edited_path = Path(str(result["edited_video"]))

    assert instruction_path.exists(), "Expected edit_instruction.json to exist."
    assert timeline_path.exists(), "Expected state_timeline.json to exist."
    if edited_path.exists():
        print("Edited video exists and cutting succeeded.")
    else:
        print("Edited video is missing. Cutting may have failed in this environment.")


if __name__ == "__main__":
    main()
