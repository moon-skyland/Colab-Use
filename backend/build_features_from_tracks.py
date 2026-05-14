"""Legacy bridge script.

Use `backend/build_features_from_video.py` for the integrated
Part 2 -> Part 3 feature-building pipeline.
"""


def main() -> None:
    print(
        "This script is deprecated. Use:\n"
        "python backend/build_features_from_video.py "
        "--video backend/data/raw_videos/sample.mp4 "
        "--court-corners-json backend/data/court_corners/sample_court_corners.json "
        "--output backend/data/features/features_inference.csv"
    )


if __name__ == "__main__":
    main()
