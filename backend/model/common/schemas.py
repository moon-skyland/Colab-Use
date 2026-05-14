"""Shared schemas for the badminton AI editor pipeline."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BoundingBox:
    """Axis-aligned bounding box in pixel coordinates."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        """Bounding box width in pixels."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Bounding box height in pixels."""
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        """Center point in pixel coordinates."""
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


@dataclass
class Detection:
    """Generic detection output."""

    frame_index: int
    label: str
    confidence: float
    bbox: BoundingBox


@dataclass
class AthleteDetection:
    """Athlete detection output for a single frame."""

    frame_index: int
    confidence: float
    bbox: BoundingBox


@dataclass
class ShuttlecockDetection:
    """Shuttlecock detection output for a single frame."""

    frame_index: int
    confidence: float
    bbox: BoundingBox
    center_pixel: tuple[float, float]


@dataclass
class AthleteTrackPoint:
    """Tracked athlete point in pixel space."""

    frame_index: int
    track_id: int
    bbox: BoundingBox
    feet_pixel: tuple[float, float]
    speed_pixel_per_frame: Optional[float]


@dataclass
class ShuttlecockTrackPoint:
    """Tracked shuttlecock point in pixel space."""

    frame_index: int
    visible: bool
    ball_pixel: Optional[tuple[float, float]]
    predicted_pixel: Optional[tuple[float, float]]
    speed_pixel_per_frame: Optional[float]
    missing_count: int


@dataclass
class CourtCoordinateSystem:
    """Definition of the badminton court coordinate system."""

    unit: str = "meters"
    court_width: float = 6.1
    court_length: float = 13.4
    origin: str = "top_left_corner"
    x_axis: str = "left_to_right"
    y_axis: str = "far_side_to_near_side"


@dataclass
class CourtZone:
    """Named polygon zone on the badminton court."""

    name: str
    polygon: list[tuple[float, float]]


@dataclass
class CourtMappingResult:
    """Court mapping calibration result."""

    coordinate_system: CourtCoordinateSystem
    homography_matrix: list[list[float]]
    zones: list[CourtZone]


@dataclass
class AthleteCourtPosition:
    """Athlete position mapped into court coordinates."""

    frame_index: int
    track_id: int
    feet_court: tuple[float, float]
    zone: Optional[str]
    in_service_zone: bool
    speed_meters_per_second: Optional[float]


@dataclass
class ShuttlecockCourtPosition:
    """Shuttlecock position mapped into court coordinates."""

    frame_index: int
    visible: bool
    ball_court: Optional[tuple[float, float]]
    inside_court: Optional[bool]
    speed_meters_per_second: Optional[float]
    missing_count: int


@dataclass
class FeatureRow:
    """Feature row for one time window."""

    video: str
    start: float
    end: float
    ball_visible_ratio: float
    ball_mean_speed: float
    ball_max_speed: float
    ball_missing_gap: int
    player_mean_speed: float
    player_max_speed: float
    players_in_service_zone: int
    players_movement_score: float


@dataclass
class LabeledFeatureRow(FeatureRow):
    """Feature row with supervised state label."""

    state: str


@dataclass
class StatePrediction:
    """Predicted state for a time window.

    Allowed states:
    - DEAD_TIME
    - READY_TO_SERVE
    - RALLY_ACTIVE
    - RALLY_ENDING
    """

    start: float
    end: float
    state: str
    confidence: Optional[float]


@dataclass
class StateSegment:
    """Merged state segment over a continuous interval."""

    start: float
    end: float
    state: str
    confidence: Optional[float]


@dataclass
class KeepInterval:
    """Video interval that should be kept in final edit."""

    start: float
    end: float
    reason: Optional[str]


@dataclass
class EditInstruction:
    """Instruction set for trimming the video."""

    video_path: str
    output_path: str
    keep_intervals: list[KeepInterval]
    version: str = "1.0"
    settings: Optional[dict] = None
