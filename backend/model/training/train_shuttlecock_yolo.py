import shutil
import csv
from pathlib import Path

from ultralytics import YOLO


################-------------
################---------------------------
def train_shuttlecock_yolo(
    data_yaml_path: str = "data/shuttle_dataset_test/data.yaml",
    base_model="yolov8n.pt", epochs: int = 50, imgsz: int = 640
) -> None:
    """Train YOLO shuttlecock detector."""
    yaml_path = Path(data_yaml_path).expanduser()
    if not yaml_path.exists():
        raise FileNotFoundError(f"Dataset YAML not found: {yaml_path}")

    _print_section("DATASET PREPROCESSING")
    prep = _preprocess_missing_empty_labels(yaml_path)
    print(f"dataset root: {prep['dataset_root']}")
    print(f"total images checked: {prep['total_images']}")
    print(f"existing label files: {prep['existing_labels']}")
    print(f"new empty labels created: {prep['created_empty_labels']}")

    # Part 1: Training
    _print_section("TRAINING")
    model = YOLO(base_model)

    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        task="detect",
        verbose=True,
    )

    best_pt = Path(results.save_dir) / "weights" / "best.pt"

    output_path = Path("backend/models/shuttlecock_yolo.pt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(best_pt, output_path)

    # Part 2: Printing
    _print_section("RESULTS")
    print(f"Trained model copied to: {output_path}")
    _print_compact_metrics(Path(results.save_dir) / "results.csv", yaml_path)
################---------------------------
################-------------


def _print_section(title: str) -> None:
    line = "=" * 30
    print(f"\n{line}\n{title}\n{line}")


def _resolve_dataset_root(data_yaml_path: Path, root_raw: str) -> Path:
    root_candidate = Path(root_raw).expanduser()
    if root_candidate.is_absolute():
        return root_candidate.resolve()
    cwd_resolved = root_candidate.resolve()
    if cwd_resolved.exists():
        return cwd_resolved
    return (data_yaml_path.parent / root_candidate).resolve()


def _iter_split_images(dataset_root: Path, split_value: str) -> list[Path]:
    split_path = Path(split_value).expanduser()
    if not split_path.is_absolute():
        split_path = (dataset_root / split_path).resolve()

    if split_path.is_file():
        image_paths: list[Path] = []
        for raw_line in split_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            candidate = Path(line).expanduser()
            if not candidate.is_absolute():
                candidate = (dataset_root / candidate).resolve()
            image_paths.append(candidate)
        return image_paths

    if split_path.is_dir():
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
        return sorted(
            p for p in split_path.rglob("*")
            if p.is_file() and p.suffix.lower() in exts
        )

    return []


def _infer_label_path(image_path: Path, dataset_root: Path) -> Path:
    image_str = str(image_path)
    if "/images/" in image_str:
        return Path(image_str.replace("/images/", "/labels/")).with_suffix(".txt")
    if "/image/" in image_str:
        return Path(image_str.replace("/image/", "/labels/")).with_suffix(".txt")

    try:
        rel = image_path.relative_to(dataset_root)
        return (dataset_root / "labels" / rel.parent / f"{image_path.stem}.txt").resolve()
    except ValueError:
        return image_path.with_suffix(".txt")


def _preprocess_missing_empty_labels(data_yaml_path: Path) -> dict[str, int]:
    payload = _parse_simple_yaml(data_yaml_path)
    root_raw = payload.get("path")
    if not root_raw:
        raise ValueError(f"'path' missing in dataset YAML: {data_yaml_path}")

    dataset_root = _resolve_dataset_root(data_yaml_path, root_raw)
    split_keys = [key for key in ("train", "val", "test") if payload.get(key)]
    if not split_keys:
        raise ValueError(
            f"At least one split (train/val/test) must be defined in {data_yaml_path}"
        )

    total_images = 0
    existing_labels = 0
    created_empty_labels = 0

    for split_key in split_keys:
        split_value = payload.get(split_key, "")
        images = _iter_split_images(dataset_root, split_value)
        total_images += len(images)
        for image_path in images:
            label_path = _infer_label_path(image_path, dataset_root)
            if label_path.exists():
                existing_labels += 1
                continue
            label_path.parent.mkdir(parents=True, exist_ok=True)
            label_path.write_text("", encoding="utf-8")
            created_empty_labels += 1

    return {
        "dataset_root": str(dataset_root),
        "total_images": total_images,
        "existing_labels": existing_labels,
        "created_empty_labels": created_empty_labels,
    }


def _parse_simple_yaml(yaml_path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in yaml_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _count_val_instances(data_yaml_path: Path) -> int:
    payload = _parse_simple_yaml(data_yaml_path)
    root_raw = payload.get("path")
    val_raw = payload.get("val")
    if not root_raw or not val_raw:
        return 0

    dataset_root = _resolve_dataset_root(data_yaml_path, root_raw)
    val_images = (dataset_root / Path(val_raw)).resolve()

    # Ultralytics convention: images -> labels
    val_labels = Path(str(val_images).replace("/images/", "/labels/"))
    if "/image/" in str(val_labels):
        val_labels = Path(str(val_labels).replace("/image/", "/labels/"))

    if not val_labels.exists():
        return 0

    total = 0
    for label_file in val_labels.glob("*.txt"):
        lines = [
            line.strip()
            for line in label_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        total += len(lines)
    return total


def _to_float(row: dict[str, str], key: str) -> float:
    raw = row.get(key, "")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _estimate_tp_fp_fn(precision: float, recall: float, gt_instances: int) -> tuple[int, int, int]:
    tp = max(0.0, recall * gt_instances)
    fn = max(0.0, gt_instances - tp)
    if precision <= 0.0:
        fp = 0.0 if tp == 0.0 else tp
    else:
        fp = max(0.0, tp * (1.0 / precision - 1.0))
    return int(round(tp)), int(round(fp)), int(round(fn))


def _print_compact_metrics(results_csv_path: Path, data_yaml_path: Path) -> None:
    if not results_csv_path.exists():
        print(f"[metrics] results.csv not found: {results_csv_path}")
        return

    gt_instances = _count_val_instances(data_yaml_path)
    with results_csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print(f"[metrics] no rows in: {results_csv_path}")
        return

    header_fmt = (
        "{epoch:>5} | {box_loss:>8} | {cls_loss:>8} | {dfl_loss:>8} | "
        "{p:>6} | {r:>6} | {map50:>7} | {map50_95:>9} | {tp:>3} | {fp:>3} | {fn:>3}"
    )
    row_fmt = (
        "{epoch:>5d} | {box_loss:>8.4f} | {cls_loss:>8.4f} | {dfl_loss:>8.4f} | "
        "{p:>6.4f} | {r:>6.4f} | {map50:>7.4f} | {map50_95:>9.4f} | {tp:>3d} | {fp:>3d} | {fn:>3d}"
    )

    print("\nCompact metrics per epoch")
    header_line = header_fmt.format(
        epoch="epoch",
        box_loss="box_loss",
        cls_loss="cls_loss",
        dfl_loss="dfl_loss",
        p="P",
        r="R",
        map50="mAP50",
        map50_95="mAP50-95",
        tp="TP",
        fp="FP",
        fn="FN",
    )
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        epoch = int(_to_float(row, "epoch"))
        box_loss = _to_float(row, "train/box_loss")
        cls_loss = _to_float(row, "train/cls_loss")
        dfl_loss = _to_float(row, "train/dfl_loss")
        precision = _to_float(row, "metrics/precision(B)")
        recall = _to_float(row, "metrics/recall(B)")
        map50 = _to_float(row, "metrics/mAP50(B)")
        map50_95 = _to_float(row, "metrics/mAP50-95(B)")
        tp, fp, fn = _estimate_tp_fp_fn(precision, recall, gt_instances)

        print(
            row_fmt.format(
                epoch=epoch,
                box_loss=box_loss,
                cls_loss=cls_loss,
                dfl_loss=dfl_loss,
                p=precision,
                r=recall,
                map50=map50,
                map50_95=map50_95,
                tp=tp,
                fp=fp,
                fn=fn,
            )
        )

    print(
        f"[metrics] TP/FP/FN estimated from P/R with val GT count={gt_instances}.\n"
    )






if __name__ == "__main__":
    train_shuttlecock_yolo()