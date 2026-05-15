"""Part 2 smoke test for detector + tracker modules."""

from pathlib import Path

SAMPLE_VIDEO = "data/raw_videos/sample.mp4"


def main() -> None:
    video_path = Path(SAMPLE_VIDEO)
    if not video_path.exists():
        print(
            "Sample video not found. Put a test video at "
            "data/raw_videos/sample.mp4"
        )
        return

    from model.common.video_utils import get_video_info, iter_video_frames
    from model.tracking.athlete_tracker import AthleteTracker
    from model.tracking.shuttlecock_tracker import ShuttlecockTracker
    from model.vision.athlete_detector import AthleteDetector
    from model.vision.shuttlecock_detector import ShuttlecockDetector

    info = get_video_info(str(video_path))
    print(f"Video info: {info}")

    athlete_detector = AthleteDetector()
    athlete_tracker = AthleteTracker()
    shuttlecock_detector = ShuttlecockDetector()
    shuttlecock_tracker = ShuttlecockTracker()

    frames_processed = 0
    athlete_detection_count = 0
    athlete_track_point_count = 0
    shuttlecock_detection_count = 0
    shuttlecock_visible_frames = 0

    for frame_index, frame in iter_video_frames(str(video_path)):
        if frames_processed >= 30:
            break

        athlete_detections = athlete_detector.detect_frame(frame, frame_index)
        athlete_tracks = athlete_tracker.update(athlete_detections)

        shuttle_detections = shuttlecock_detector.detect_frame(frame, frame_index)
        shuttle_track = shuttlecock_tracker.update(shuttle_detections, frame_index)

        frames_processed += 1
        athlete_detection_count += len(athlete_detections)
        athlete_track_point_count += len(athlete_tracks)
        shuttlecock_detection_count += len(shuttle_detections)
        if shuttle_track.visible:
            shuttlecock_visible_frames += 1

    print(f"frames processed: {frames_processed}")
    print(f"athlete detections: {athlete_detection_count}")
    print(f"athlete track points: {athlete_track_point_count}")
    print(f"shuttlecock detections: {shuttlecock_detection_count}")
    print(f"shuttlecock visible frames: {shuttlecock_visible_frames}")


if __name__ == "__main__":
    main()
