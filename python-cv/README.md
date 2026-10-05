# Fatigue CV Worker

This directory contains the Python CV worker for the pilot fatigue system (Step 5A).
It handles face landmark extraction and geometric analysis independently of the Next.js UI.

## Modules
- `config/`: Application settings and thresholds.
- `camera/`: Handles physical video capture (OpenCV wrapper).
- `detection/`: Isolates MediaPipe inferences. Produces framework-free Cartesian coordinates.
- `features/`: Mathematical geometric extraction (EAR, MAR, Head Pose) from agnostic coordinates.
- `transport/`: Outputs structured JSON telemetry to `stdout`.

## Setup
```bash
cd python-cv
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Unix
source .venv/bin/activate

pip install .[test]
```

## Running Tests
Ensure the virtual environment is active, then run:
```bash
pytest
```
