import shutil
from pathlib import Path

from ultralytics import YOLO

def train_shuttlecock_yolo(
    data_yaml_path: str = "data/shuttle_dataset_test/data.yaml",
    base_model="yolov8n.pt", epochs: int = 50, imgsz: int = 640
) -> None:
    """Train YOLO shuttlecock detector."""
    yaml_path = Path(data_yaml_path).expanduser()
    if not yaml_path.exists():
        raise FileNotFoundError(f"Dataset YAML not found: {yaml_path}")

    model = YOLO(base_model)

    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        task="detect"
    )

    best_pt = Path(results.save_dir) / "weights" / "best.pt"

    output_path = Path("backend/models/shuttlecock_yolo.pt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(best_pt, output_path)

    print(f"Trained model copied to: {output_path}")

if __name__ == "__main__":
    train_shuttlecock_yolo()