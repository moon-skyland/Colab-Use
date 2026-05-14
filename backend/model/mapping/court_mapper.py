"""Court mapping with basic homography calibration."""

import cv2
import numpy as np

from model.common.schemas import CourtCoordinateSystem, CourtMappingResult, CourtZone


class CourtMapper:
    """Calibrates and maps pixel coordinates to court coordinates."""

    def __init__(self) -> None:
        self.coordinate_system = CourtCoordinateSystem()
        self.H: np.ndarray | None = None
        self.zones: list[CourtZone] = []
        self._calibrated = False
        self.meters_per_pixel = 1.0

    def calibrate(self, image_points: list[tuple[float, float]]) -> CourtMappingResult:
        """Calibrate court mapping.

        Input: four court corner points in image pixel coordinates.
        Output: court coordinate system, homography matrix, court zones.
        """
        if len(image_points) != 4:
            raise ValueError(
                "Court calibration needs exactly 4 points in order "
                "[top_left, top_right, bottom_right, bottom_left]."
            )

        src_points = np.array(image_points, dtype=np.float32)
        dst_points = np.array(
            [
                [0.0, 0.0],
                [self.coordinate_system.court_width, 0.0],
                [
                    self.coordinate_system.court_width,
                    self.coordinate_system.court_length,
                ],
                [0.0, self.coordinate_system.court_length],
            ],
            dtype=np.float32,
        )

        homography, _ = cv2.findHomography(src_points, dst_points)
        if homography is None:
            raise ValueError("Failed to estimate homography from provided image points.")
        self.H = homography.astype(np.float32)
        self._calibrated = True

        # Basic scale estimate to convert pixel/frame speed -> meter/second.
        top_px = float(np.linalg.norm(src_points[1] - src_points[0]))
        left_px = float(np.linalg.norm(src_points[3] - src_points[0]))
        width_scale = self.coordinate_system.court_width / max(top_px, 1e-6)
        length_scale = self.coordinate_system.court_length / max(left_px, 1e-6)
        self.meters_per_pixel = (width_scale + length_scale) / 2.0

        self.zones = self.build_default_zones()
        return CourtMappingResult(
            coordinate_system=self.coordinate_system,
            homography_matrix=self.H.tolist(),
            zones=self.zones,
        )

    def pixel_to_court(self, point: tuple[float, float]) -> tuple[float, float]:
        """Map one pixel point to court coordinates.

        Input: one point in image pixel coordinates.
        Output: one point in court coordinates.
        """
        if not self._calibrated or self.H is None:
            raise RuntimeError(
                "CourtMapper is not calibrated. Call calibrate() with 4 court corners first."
            )

        src = np.array([[[point[0], point[1]]]], dtype=np.float32)
        mapped = cv2.perspectiveTransform(src, self.H)
        return float(mapped[0, 0, 0]), float(mapped[0, 0, 1])

    def build_default_zones(self) -> list[CourtZone]:
        """Build approximate named court zones in meter coordinates."""
        width = self.coordinate_system.court_width
        length = self.coordinate_system.court_length
        center_x = width / 2.0
        net_y = length / 2.0

        return [
            CourtZone(
                name="full_court",
                polygon=[(0.0, 0.0), (width, 0.0), (width, length), (0.0, length)],
            ),
            CourtZone(
                name="far_left_service",
                polygon=[(0.0, 0.0), (center_x, 0.0), (center_x, net_y), (0.0, net_y)],
            ),
            CourtZone(
                name="far_right_service",
                polygon=[(center_x, 0.0), (width, 0.0), (width, net_y), (center_x, net_y)],
            ),
            CourtZone(
                name="near_left_service",
                polygon=[(0.0, net_y), (center_x, net_y), (center_x, length), (0.0, length)],
            ),
            CourtZone(
                name="near_right_service",
                polygon=[(center_x, net_y), (width, net_y), (width, length), (center_x, length)],
            ),
        ]

    def point_in_zone(self, point: tuple[float, float], zone: CourtZone) -> bool:
        """Check whether a court point lies inside a zone polygon."""
        contour = np.array(zone.polygon, dtype=np.float32).reshape((-1, 1, 2))
        result = cv2.pointPolygonTest(contour, point, False)
        return result >= 0

    def find_zone(self, point: tuple[float, float]) -> str | None:
        """Find first matching zone name for a court point."""
        for zone in self.zones:
            if self.point_in_zone(point, zone):
                return zone.name
        return None

    def pixel_speed_to_mps(self, speed_pixel_per_frame: float | None, fps: float) -> float | None:
        """Convert speed from pixel/frame to meter/second."""
        if speed_pixel_per_frame is None:
            return None
        return float(speed_pixel_per_frame * self.meters_per_pixel * fps)
