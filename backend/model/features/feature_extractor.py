"""Feature extraction logic for Part 3 state modeling."""

from collections import defaultdict
from statistics import mean

from model.common.schemas import (
    AthleteCourtPosition,
    FeatureRow,
    ShuttlecockCourtPosition,
)


class FeatureExtractor:
    """Extracts model features from mapped trajectories."""

    def extract_window_features(
        self,
        video_name: str,
        start: float,
        end: float,
        athlete_positions: list[AthleteCourtPosition],
        shuttlecock_positions: list[ShuttlecockCourtPosition],
    ) -> FeatureRow:
        """Extract one feature row for a time window.

        Input: athlete court positions and shuttlecock court positions in a time window.
        Output: one FeatureRow.
        """
        total_shuttle = len(shuttlecock_positions)
        visible_shuttle = sum(1 for point in shuttlecock_positions if point.visible)
        ball_visible_ratio = (
            float(visible_shuttle) / float(total_shuttle) if total_shuttle > 0 else 0.0
        )

        ball_speeds = [
            point.speed_meters_per_second
            for point in shuttlecock_positions
            if point.visible and point.speed_meters_per_second is not None
        ]
        player_speeds = [
            point.speed_meters_per_second
            for point in athlete_positions
            if point.speed_meters_per_second is not None
        ]
        players_in_service_zone = len(
            {point.track_id for point in athlete_positions if point.in_service_zone}
        )
        player_mean_speed = float(mean(player_speeds)) if player_speeds else 0.0
        player_movement_score = min(player_mean_speed / 5.0, 1.0) if player_mean_speed > 0 else 0.0

        return FeatureRow(
            video=video_name,
            start=start,
            end=end,
            ball_visible_ratio=ball_visible_ratio,
            ball_mean_speed=float(mean(ball_speeds)) if ball_speeds else 0.0,
            ball_max_speed=float(max(ball_speeds)) if ball_speeds else 0.0,
            ball_missing_gap=max(
                (point.missing_count for point in shuttlecock_positions), default=0
            ),
            player_mean_speed=player_mean_speed,
            player_max_speed=float(max(player_speeds)) if player_speeds else 0.0,
            players_in_service_zone=players_in_service_zone,
            players_movement_score=player_movement_score,
        )

    def extract_features(
        self,
        video_name: str,
        athlete_positions: list[AthleteCourtPosition],
        shuttlecock_positions: list[ShuttlecockCourtPosition],
        fps: float,
        window_size_seconds: float = 1.0,
    ) -> list[FeatureRow]:
        """Extract numeric feature rows over fixed frame windows.

        Input:
        - video_name: source video name
        - athlete_positions: athlete court positions with frame indices
        - shuttlecock_positions: shuttlecock court positions with frame indices
        - fps: frames per second
        - window_size_seconds: window duration in seconds

        Output:
        - list[FeatureRow], one per time window.
        """
        if fps <= 0:
            raise ValueError("fps must be positive for feature extraction.")
        if window_size_seconds <= 0:
            raise ValueError("window_size_seconds must be positive.")

        all_frame_indices = [p.frame_index for p in athlete_positions] + [
            p.frame_index for p in shuttlecock_positions
        ]
        if not all_frame_indices:
            return []

        window_size_frames = max(1, int(round(window_size_seconds * fps)))
        min_frame = min(all_frame_indices)
        max_frame = max(all_frame_indices)

        athlete_by_window: dict[int, list[AthleteCourtPosition]] = defaultdict(list)
        shuttle_by_window: dict[int, list[ShuttlecockCourtPosition]] = defaultdict(list)

        for point in athlete_positions:
            window_idx = (point.frame_index - min_frame) // window_size_frames
            athlete_by_window[window_idx].append(point)
        for point in shuttlecock_positions:
            window_idx = (point.frame_index - min_frame) // window_size_frames
            shuttle_by_window[window_idx].append(point)

        total_windows = ((max_frame - min_frame) // window_size_frames) + 1
        feature_rows: list[FeatureRow] = []

        for window_idx in range(total_windows):
            window_start_frame = min_frame + (window_idx * window_size_frames)
            window_end_exclusive = window_start_frame + window_size_frames

            row = self.extract_window_features(
                video_name=video_name,
                start=window_start_frame / fps,
                end=min(window_end_exclusive, max_frame + 1) / fps,
                athlete_positions=athlete_by_window.get(window_idx, []),
                shuttlecock_positions=shuttle_by_window.get(window_idx, []),
            )
            feature_rows.append(row)

        return feature_rows

    def extract_features_over_time(
        self,
        video_name: str,
        athlete_positions: list[AthleteCourtPosition],
        shuttlecock_positions: list[ShuttlecockCourtPosition],
        fps: float,
        window_seconds: float = 1.0,
    ) -> list[FeatureRow]:
        """Backward-compatible alias for extract_features()."""
        return self.extract_features(
            video_name=video_name,
            athlete_positions=athlete_positions,
            shuttlecock_positions=shuttlecock_positions,
            fps=fps,
            window_size_seconds=window_seconds,
        )
