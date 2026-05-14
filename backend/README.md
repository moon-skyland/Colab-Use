# Badminton AI Editor Backend (Part 1-5)

This folder contains the backend implementation for Part 1 to Part 5 of the badminton AI video editor.

## Scope in Part 1

- Create clean backend project structure.
- Define shared schemas/dataclasses for all pipeline stages.
- Add placeholder modules with clear input/output interfaces.
- Avoid heavy CV/model logic until later parts.

## Part 2 Implemented

- Athlete Detector using pretrained YOLO person class.
- Shuttlecock Detector using `backend/models/shuttlecock_yolo.pt` if available.
- Empty/mock mode for shuttlecock detection when model file is missing.
- Simple nearest-neighbor Athlete Tracker.
- Simple missing-frame-tolerance Shuttlecock Tracker.
- Court Mapper using manual four-corner calibration and homography.
- Court Position Converter for athlete/shuttlecock pixel-to-court conversion.
- Basic video utilities in `model/common/video_utils.py`.
- Part 2 smoke test script: `backend/test_part2_pipeline.py`.

## Part 3 Implemented

- `FeatureExtractor` for numeric window features from court positions.
- Feature CSV writer/reader utilities.
- `StateLabeler` for attaching manual state label JSON to feature windows.
- RandomForest state model training (`train_state_model.py`).
- `StatePredictor` for inference from feature rows/CSV.
- Synthetic Part 3 demo script: `backend/test_part3_state_model.py`.

## Part 4 Implemented

- `TimelineBuilder` for converting state predictions into continuous state timeline.
- Timeline smoothing for short noisy segments.
- `instruction_generator.py` generates `EditInstruction` objects from `StateSegment` timelines.
- `instruction_utils.py` saves, loads, validates, and merges edit instructions.
- `build_instruction_from_predictions.py` connects `TimelineBuilder` + `InstructionGenerator` + `instruction_utils` to produce `edit_instruction.json`.
- Synthetic Part 4 test script (`backend/test_part4_instruction.py`).

### Part 4 File Flow

`state_predictions.csv`  
-> `state_timeline.json`  
-> `edit_instruction.json`

### Edit Instruction Format

```json
{
  "version": "1.0",
  "video_path": "...",
  "output_path": "...",
  "keep_intervals": [
    { "start": 5.0, "end": 19.0, "reason": "rally_active_with_context" }
  ]
}
```

`cut_video.py` in **Part 5** will load `edit_instruction.json` via `instruction_utils.py`
and then perform actual video cutting.

## Part 5 Implemented

- Real video cutting in `model/editing/cut_video.py` using keep intervals from edit instruction.
- End-to-end pipeline runner: `backend/run_backend_pipeline.py`.
- FastAPI backend upload/process/status/download/cleanup flow in `backend/app.py`.
- Integration script pipeline:
  - upload raw video
  - build features
  - predict states
  - build timeline + instruction
  - cut edited video
- Minimal frontend integration updates for displaying keep intervals as time ranges.
- Real `VideoCutter`.
- `pipeline.py` unified backend flow.
- FastAPI backend API (`backend/api.py`).
- Upload/process endpoints.
- Static output serving (`/outputs` and `/uploads`).
- Minimal frontend flow.
- End-to-end demo test script.

## Training vs Product Use

- **Training flow**
  - `features_train.csv` includes a `state` column.
  - Features + state labels -> train model -> `backend/models/state_model.pkl`.
- **Product flow**
  - `features_inference.csv` does not include a `state` column.
  - Features only + trained model -> predicted state (`predicted_state`).

## YOLO vs State Model Data

- State Model does **not** use YOLO `data.yaml`.
- YOLO training uses images + `.txt` detection labels + `data.yaml`.
- State Model training uses tabular CSV features + scikit-learn.

## Folder Responsibilities

- `backend/model/`: Python AI/video pipeline code (detectors, tracking, mapping, features, state pipeline, editing).
- `backend/models/`: trained model files and weights (for example `shuttlecock_yolo.pt` and `state_model.pkl`).
- `backend/data/`: raw/processed videos, training data, labels, and extracted features.
- `backend/outputs/`: generated artifacts such as timelines, instructions, and edited outputs.

## Training Needed Later

- Shuttlecock Detector (custom detector training).
- State Model (state classification model training).

## No Training Needed (Rule/Algorithm Based)

- Athlete Detector uses pretrained YOLO person class.
- Athlete/Shuttlecock trackers are algorithmic logic.
- Court Mapper uses homography-based mapping.
- Instruction Generator and Video Cutter are rule/video-processing logic.

## Model and Algorithm Notes

- Shuttlecock detector still needs a trained YOLO model for real performance.
- Athlete detector does not need custom training because it uses pretrained person detection.
- Trackers are algorithms and do not require model training.
- Court mapper is geometry/homography logic and does not require model training.

## Planned in Later Parts

- (Final polishing only) model quality improvements, production hardening, and UX refinements.

## Run Import Check

From `backend/`:

```bash
python main.py
```

Expected output:

```text
Badminton AI Editor backend skeleton is ready.
```

## Part 3 Commands

Train on real features:

```bash
python backend/model/training/train_state_model.py \
  --features backend/data/features/features_train.csv \
  --output backend/models/state_model.pkl
```

Run synthetic demo:

```bash
python backend/test_part3_state_model.py
```

Build inference features from raw video (Part 2 -> Part 3 bridge):

```bash
python backend/build_features_from_video.py \
  --video backend/data/raw_videos/sample.mp4 \
  --court-corners-json backend/data/court_corners/sample_court_corners.json \
  --output backend/data/features/features_inference.csv \
  --max-frames 300
```

Note: `backend/data/court_corners/sample_court_corners.json` contains placeholder points.
Replace them with real court corner pixel coordinates from your actual video.

## Part 4 Commands

Run synthetic Part 4 test:

```bash
python backend/test_part4_instruction.py
```

Build instruction from predictions:

```bash
python backend/build_instruction_from_predictions.py \
  --predictions backend/outputs/state_predictions.csv \
  --video backend/data/raw_videos/sample.mp4 \
  --output-video backend/outputs/edited_video.mp4 \
  --timeline-output backend/outputs/state_timeline.json \
  --instruction-output backend/outputs/edit_instruction.json
```

## Part 5 Commands

Run full backend pipeline directly:

```bash
python backend/run_backend_pipeline.py \
  --video backend/data/raw_videos/sample.mp4 \
  --output-video backend/outputs/edited_video.mp4 \
  --court-corners-json backend/data/court_corners/sample_court_corners.json
```

Run FastAPI server:

```bash
python backend/app.py
```

Run backend (preferred):

```bash
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

Backend URL:

```text
http://localhost:8000
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Run backend:

```bash
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Run backend end-to-end test:

```bash
python backend/test_part5_end_to_end.py
```

### Important Part 5 Files

- `backend/api.py`
- `backend/pipeline.py`
- `backend/model/editing/cut_video.py`
- `frontend/src/App.jsx`

### Final Product Flow

Upload video -> process -> preview original -> preview edited -> download edited.

### Current Limitations

- If `shuttlecock_yolo.pt` is missing, shuttlecock detector uses mock/empty mode.
- If `state_model.pkl` is missing, state predictor may use mock mode.
- Court corners are currently placeholder unless user provides real calibration.
- Output quality depends on trained models and real court calibration.
