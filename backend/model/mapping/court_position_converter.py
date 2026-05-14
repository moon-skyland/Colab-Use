"""Convert tracked pixel positions into court coordinates."""

from model.common.schemas import (
    AthleteCourtPosition,
    AthleteTrackPoint,
    ShuttlecockCourtPosition,
    ShuttlecockTrackPoint,
)
from model.mapping.court_mapper import CourtMapper


class CourtPositionConverter:
    """Converts athlete and shuttlecock tracks using a calibrated CourtMapper."""

    def convert_athletes(
        self,
        athlete_tracks: list[AthleteTrackPoint],
        court_mapper: CourtMapper,
    ) -> list[AthleteCourtPosition]:
        """Convert athlete tracks from pixel space to court space."""
        outputs: list[AthleteCourtPosition] = []
        for track in athlete_tracks:
            feet_court = court_mapper.pixel_to_court(track.feet_pixel)
            zone = court_mapper.find_zone(feet_court)
            outputs.append(
                AthleteCourtPosition(
                    frame_index=track.frame_index,
                    track_id=track.track_id,
                    feet_court=feet_court,
                    zone=zone,
                    in_service_zone=bool(zone and "service" in zone),
                    speed_meters_per_second=None,
                )
            )
        return outputs

    def convert_shuttlecock(
        self,
        shuttle_tracks: list[ShuttlecockTrackPoint],
        court_mapper: CourtMapper,
    ) -> list[ShuttlecockCourtPosition]:
        """Convert shuttlecock tracks from pixel space to court space."""
        outputs: list[ShuttlecockCourtPosition] = []
        for track in shuttle_tracks:
            if track.visible and track.ball_pixel is not None:
                ball_court = court_mapper.pixel_to_court(track.ball_pixel)
                inside_court = court_mapper.find_zone(ball_court) == "full_court"
            else:
                ball_court = None
                inside_court = None

            outputs.append(
                ShuttlecockCourtPosition(
                    frame_index=track.frame_index,
                    visible=track.visible,
                    ball_court=ball_court,
                    inside_court=inside_court,
                    speed_meters_per_second=None,
                    missing_count=track.missing_count,
                )
            )
        return outputs
