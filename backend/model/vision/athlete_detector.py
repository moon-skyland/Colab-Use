"""Athlete detector backed by pretrained Ultralytics YOLO."""

from typing import Any

from model.common.schemas import AthleteDetection, BoundingBox


class AthleteDetector:
    """Detects athletes from video frames.

    This uses COCO class 0 (person) from a pretrained YOLO model.
    """

    def __init__(
        self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.35
    ) -> None:
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        try:
            from ultralytics import YOLO

            self.model = YOLO(model_name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load YOLO model '{model_name}'. "
                "Ensure ultralytics is installed and model weights are available."
            ) from exc

    def detect_frame(self, frame: Any, frame_index: int) -> list[AthleteDetection]:
        """Run athlete detection on one frame.

        Input: one video frame as numpy array.
        Output: person/athlete bounding boxes for that frame.
        """
        if frame is None:
            return []

        results = self.model.predict(
            source=frame,
            classes=[0],  # COCO person class
            conf=self.confidence_threshold,
            verbose=False,
        )
        if not results:
            return []

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []

        detections: list[AthleteDetection] = []
        for box in boxes:
            confidence = float(box.conf.item())
            if confidence < self.confidence_threshold:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(
                AthleteDetection(
                    frame_index=frame_index,
                    confidence=confidence,
                    bbox=BoundingBox(
                        x1=float(x1),
                        y1=float(y1),
                        x2=float(x2),
                        y2=float(y2),
                    ),
                )
            )

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections
