"""Shuttlecock tracker with missing-frame tolerance.

Designed to be upgrade-friendly for future Kalman filter integration.
"""

import math

from model.common.schemas import ShuttlecockDetection, ShuttlecockTrackPoint


class ShuttlecockTracker:
    """Tracks shuttlecock trajectory over time."""

    def __init__(self, max_missing_frames: int = 10) -> None:
        self.max_missing_frames = max_missing_frames
        self.last_ball_pixel: tuple[float, float] | None = None
        self.last_frame_index: int | None = None
        self.missing_count: int = 0

    def update(
        self, detections: list[ShuttlecockDetection], frame_index: int
    ) -> ShuttlecockTrackPoint:
        """Update shuttlecock track state.

        Input: shuttlecock detections for current frame.
        Output: ball trajectory point with visibility, position, speed, missing_count.
        """
        if detections:
            best = max(detections, key=lambda d: d.confidence)
            ball_pixel = best.center_pixel
            speed = None

            if self.last_ball_pixel is not None and self.last_frame_index is not None:
                frame_gap = max(1, frame_index - self.last_frame_index)
                speed = math.dist(ball_pixel, self.last_ball_pixel) / float(frame_gap)

            self.last_ball_pixel = (float(ball_pixel[0]), float(ball_pixel[1]))
            self.last_frame_index = frame_index
            self.missing_count = 0

            return ShuttlecockTrackPoint(
                frame_index=frame_index,
                visible=True,
                ball_pixel=self.last_ball_pixel,
                predicted_pixel=self.last_ball_pixel,
                speed_pixel_per_frame=speed,
                missing_count=self.missing_count,
            )

        self.missing_count += 1
        predicted_pixel = (
            self.last_ball_pixel if self.missing_count <= self.max_missing_frames else None
        )

        return ShuttlecockTrackPoint(
            frame_index=frame_index,
            visible=False,
            ball_pixel=None,
            predicted_pixel=predicted_pixel,
            speed_pixel_per_frame=None,
            missing_count=self.missing_count,
        )
