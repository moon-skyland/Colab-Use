"""Shuttlecock detector backed by a custom Ultralytics YOLO model."""

from pathlib import Path
from typing import Any

from model.common.schemas import BoundingBox
from model.common.schemas import ShuttlecockDetection


class ShuttlecockDetector:
    """Detects shuttlecock from video frames.

    Uses a custom YOLO model when available. Falls back to mock mode if allowed.
    """

    def __init__(
        self,
        model_path: str = "backend/models/shuttlecock_yolo.pt",
        confidence_threshold: float = 0.25,
        mock_if_missing: bool = True,
    ) -> None:
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.mock_if_missing = mock_if_missing
        self.model = None
        self.mock_mode = False

        model_file = Path(model_path)
        if not model_file.exists():
            if mock_if_missing:
                self.mock_mode = True
                return
            raise FileNotFoundError(
                f"Shuttlecock model file not found at '{model_path}'. "
                "Set mock_if_missing=True to run in mock mode."
            )

        try:
            from ultralytics import YOLO

            self.model = YOLO(str(model_file))
        except Exception as exc:
            if mock_if_missing:
                self.mock_mode = True
                self.model = None
                return
            raise RuntimeError(
                f"Failed to load shuttlecock YOLO model from '{model_path}'. "
                "Set mock_if_missing=True to continue in mock mode."
            ) from exc

    def detect_frame(self, frame: Any, frame_index: int) -> list[ShuttlecockDetection]:
        """Run shuttlecock detection on one frame.

        Input: one video frame as numpy array.
        Output: shuttlecock bounding box detections for that frame.
        """
        if frame is None:
            return []
        if self.mock_mode:
            return []

        assert self.model is not None
        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
        )
        if not results:
            return []

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []
        detections: list[ShuttlecockDetection] = []

        for box in boxes:
            confidence = float(box.conf.item())
            if confidence < self.confidence_threshold:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            detections.append(
                ShuttlecockDetection(
                    frame_index=frame_index,
                    confidence=confidence,
                    bbox=BoundingBox(
                        x1=float(x1),
                        y1=float(y1),
                        x2=float(x2),
                        y2=float(y2),
                    ),
                    center_pixel=(float(cx), float(cy)),
                )
            )

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections
