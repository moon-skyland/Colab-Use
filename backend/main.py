"""Entry point to validate backend skeleton imports."""

from model.editing.cut_video import VideoCutter
from model.editing.instruction_generator import InstructionGenerator
from model.features.feature_extractor import FeatureExtractor
from model.mapping.court_mapper import CourtMapper
from model.segmentation.state_predictor import StatePredictor
from model.segmentation.timeline_builder import TimelineBuilder
from model.tracking.athlete_tracker import AthleteTracker
from model.tracking.shuttlecock_tracker import ShuttlecockTracker
from model.vision.athlete_detector import AthleteDetector
from model.vision.shuttlecock_detector import ShuttlecockDetector


def main() -> None:
    """Instantiate all core modules once to validate project wiring."""
    _athlete_detector = AthleteDetector()
    _shuttlecock_detector = ShuttlecockDetector()
    _athlete_tracker = AthleteTracker()
    _shuttlecock_tracker = ShuttlecockTracker()
    _court_mapper = CourtMapper()
    _feature_extractor = FeatureExtractor()
    _state_predictor = StatePredictor()
    _timeline_builder = TimelineBuilder()
    _instruction_generator = InstructionGenerator()
    _video_cutter = VideoCutter()

    _ = (
        _athlete_detector,
        _shuttlecock_detector,
        _athlete_tracker,
        _shuttlecock_tracker,
        _court_mapper,
        _feature_extractor,
        _state_predictor,
        _timeline_builder,
        _instruction_generator,
        _video_cutter,
    )

    print("Badminton AI Editor backend skeleton is ready.")


if __name__ == "__main__":
    main()
