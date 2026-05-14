"""Athlete tracker with nearest-neighbor association."""

import math
from typing import Any

from model.common.schemas import AthleteDetection, AthleteTrackPoint


class AthleteTracker:
    """Tracks detected athletes over time.

    Part 2 implementation:
    - nearest-feet matching
    - persistent track IDs
    - per-frame pixel speed estimate
    - missing-frame handling for track lifecycle
    """

    def __init__(self, max_distance: float = 80.0, max_missing_frames: int = 30) -> None:
        self.max_distance = max_distance
        self.max_missing_frames = max_missing_frames
        self.next_track_id = 1
        self.tracks: dict[int, dict[str, Any]] = {}

    def update(self, detections: list[AthleteDetection]) -> list[AthleteTrackPoint]:
        """Update athlete tracks.

        Input: athlete detections from one frame or across frames.
        Output: athlete track points with track_id, feet_pixel, and speed.
        """
        if not detections:
            for track in self.tracks.values():
                track["missing_count"] += 1
            self._prune_missing_tracks()
            return []

        frame_index = detections[0].frame_index
        matched_track_ids: set[int] = set()
        output: list[AthleteTrackPoint] = []

        # Greedy association by nearest feet distance.
        for det in detections:
            feet = ((det.bbox.x1 + det.bbox.x2) / 2.0, det.bbox.y2)
            best_track_id: int | None = None
            best_distance = float("inf")

            for track_id, track_state in self.tracks.items():
                if track_id in matched_track_ids:
                    continue
                prev_feet = track_state["last_feet_pixel"]
                distance = math.dist(feet, prev_feet)
                if distance < best_distance and distance <= self.max_distance:
                    best_distance = distance
                    best_track_id = track_id

            if best_track_id is None:
                track_id = self.next_track_id
                self.next_track_id += 1
                speed = None
                self.tracks[track_id] = {
                    "track_id": track_id,
                    "last_feet_pixel": feet,
                    "last_frame_index": frame_index,
                    "last_bbox": det.bbox,
                    "missing_count": 0,
                }
            else:
                track_id = best_track_id
                prev_feet = self.tracks[track_id]["last_feet_pixel"]
                prev_frame = self.tracks[track_id]["last_frame_index"]
                frame_gap = max(1, frame_index - prev_frame)
                speed = math.dist(feet, prev_feet) / float(frame_gap)
                self.tracks[track_id]["last_feet_pixel"] = feet
                self.tracks[track_id]["last_frame_index"] = frame_index
                self.tracks[track_id]["last_bbox"] = det.bbox
                self.tracks[track_id]["missing_count"] = 0

            matched_track_ids.add(track_id)
            output.append(
                AthleteTrackPoint(
                    frame_index=frame_index,
                    track_id=track_id,
                    bbox=det.bbox,
                    feet_pixel=(float(feet[0]), float(feet[1])),
                    speed_pixel_per_frame=speed,
                )
            )

        for track_id, track_state in self.tracks.items():
            if track_id not in matched_track_ids:
                track_state["missing_count"] += 1
        self._prune_missing_tracks()

        output.sort(key=lambda p: p.track_id)
        return output

    def _prune_missing_tracks(self) -> None:
        stale_track_ids = [
            track_id
            for track_id, state in self.tracks.items()
            if state["missing_count"] > self.max_missing_frames
        ]
        for track_id in stale_track_ids:
            del self.tracks[track_id]
