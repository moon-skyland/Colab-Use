from pathlib import Path
import shutil

def train_shuttlecock_yolo(
    data_yaml_path="backend/data/shuttle_dataset_test/data.yaml", 
    base_model="yolov8n.pt", epochs: int = 50, imgsz: int = 640
) -> None:
    """Train YOLO shuttlecock detector."""
    
    model = YOLO(base_model)

    model.train(
    data=data_yaml_path,
    epochs=epochs,
    imgsz=imgsz,
    task="detect"
    )

    best_pt = Path(model.results.save_dir) / "weights" / "best.pt"
