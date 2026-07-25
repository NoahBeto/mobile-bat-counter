# Mobile Bat Counter

Real-time thermal bat detection and counting on edge computing devices using **YOLOv11 + SORT tracking**.

Mobile Bat Counter adapts the original thermal-video bat counting pipeline from:

https://github.com/Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT

for deployment on GPU-enabled edge hardware, specifically Sage/Waggle nodes with NVIDIA Thor GPUs.

The system detects bats in thermal video using **YOLOv11**, tracks individual bats across frames using **SORT (Simple Online and Realtime Tracking)**, and produces unique bat counts without requiring researchers to manually collect and process video recordings.

---

# Overview

The original bat counting workflow required:

1. Collecting thermal camera recordings
2. Downloading videos from field deployments
3. Running detection and tracking offline
4. Reviewing generated counts

Mobile-Bat-Counter moves this processing directly onto Sage/Waggle edge devices.

The deployed system performs:

1. Thermal camera capture
2. Background subtraction
3. YOLOv11 bat detection
4. ROI filtering
5. SORT tracking
6. Unique bat counting
7. Publishing count measurements through the Sage platform

Instead of transferring large thermal video files, the edge device processes the footage locally and transmits only bat count measurements.

This enables long-term automated monitoring of bat populations through nightly data collection.

---

# Pipeline

The edge deployment pipeline runs continuously on a Sage/Waggle node:

```bash
Thermal Camera
|
v
Frame Capture
|
v
Background Subtraction
|
v
YOLOv11 Detection
|
v
ROI Filtering
|
v
SORT Tracking
|
v
Unique Bat Count
|
v
Sage Data API
|
v
Nightly Population Dataset
```

The edge device processes thermal video locally and publishes bat count measurements instead of storing or transmitting full recordings.

Each run produces a count measurement:

```bash
env.count.bat = <number_of_detected_bats>
```

These measurements can be collected over time to build nightly bat population datasets for long-term monitoring.

---

# Project Structure

```bash
mobile-bat-counter/

├── plugin/                         # Sage/Waggle edge deployment
│ ├── app.py                        # Real-time edge plugin
│ ├── Dockerfile                    # GPU container definition
│ ├── requirements.txt              # Plugin dependencies
│ ├── sage.yaml                     # Sage deployment configuration
│ ├── sort/
│ │ └── sort.py                     # SORT tracker
│ ├── sort_shim.py                  # Lightweight SORT dependency shim
│ └── models/
│   └── best.pt                     # YOLOv11 weights
│
├── videos/                         # Sample thermal videos for testing
│
├── data/                           # Generated bat count measurements
│ └── nightly_counts.csv            # Published nightly counts
│
├── models/
│ └── PB_noaug/
│   └── weights/
│       └── best.pt                 # Original YOLO weights
│
├── src/                            # Original offline pipeline code
│ ├── tracking.py
│ ├── detection.py
│ └── bg_subtract_new.py
│
├── configs/                        # Offline pipeline configurations
│ ├── videos.list
│ └── generated/
│
├── run_bat_counter.py              # Offline pipeline entry point
├── pixi.toml                       # Offline development environment
├── pixi.lock
└── README.md
```

---

# Edge Deployment (Primary Workflow)

The primary deployment workflow runs the bat counter as a GPU-enabled Sage/Waggle plugin.

The plugin runs inside a container on NVIDIA Thor edge hardware and performs real-time thermal bat detection, tracking, and count publishing.

The tested deployment environment:

- Hardware: NVIDIA Thor
- Architecture: ARM64
- GPU acceleration: NVIDIA CUDA
- Inference framework: PyTorch + YOLOv11
- Deployment platform: Sage/Waggle

The edge device performs local processing and publishes bat counts through the Sage data platform, allowing long-term automated monitoring without transferring raw thermal video.

---

## Build the Plugin

From the repository root:

```bash
sudo pluginctl build plugin/
```

This builds the Sage/Waggle plugin container image:

```bash
10.31.81.1:5000/local/plugin
```

The container includes:

- CUDA-enabled PyTorch
- YOLOv11 model weights
- SORT tracking
- Background subtraction
- Sage/Waggle data publishing support

## Test with a Sample Thermal Video

A local thermal video can be used to verify the complete edge pipeline before connecting a live camera.

Run:

```bash
podman run --rm -it \
  --name bat-counter \
  --device=nvidia.com/gpu=0 \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/configs:/app/configs \
  10.31.81.1:5000/local/plugin \
  --camera-source videos/P1.1.2_grey.mov \
  --max-frames 200 \
  --interval 0
```

Expected output:

```bash
Loading YOLO model from /app/models/best.pt onto cuda
torch.cuda.is_available()=True
...
Final unique bat count: X
Saved nightly count: X bats -> data/nightly_counts.csv
```

A successful run confirms:

- NVIDIA GPU access
- CUDA-enabled PyTorch
- YOLOv11 inference
- Background subtraction
- SORT tracking
- Bat counting
- Nightly count data collection

The generated count is stored locally:

```bash
data/nightly_counts.csv
```

Example:

```bash
timestamp,bat_count
2026-07-25T04:08:20.539841,1
```

# Camera Sources

The plugin supports three camera input modes.

## 1. Sage/Waggle Camera (Production)

Production deployments use Sage/Waggle camera names.

Example:

```bash
--camera-source bottom_camera
```

The node automatically resolves the camera stream through the Sage/Waggle camera interface.

This is the intended mode for long-term field deployments and nightly bat monitoring.

## 2. RTSP Camera

Network thermal cameras can be accessed through an RTSP stream.

Example:

```bash
--camera-source rtsp://camera-address/stream
```

Example:

```bash
sudo pluginctl run --name bat-counter <image> -- \
--camera-source rtsp://user:password@camera-ip:554/stream
```

## 3. Local Thermal Video (Testing)

Local video files can be used to validate the pipeline before deployment.

Example:

```bash
--camera-source videos/P1.1.2_grey.mov
```

For testing, limit processing using:

```bash
--max-frames <number-of-frames>
```

Example:

```bash
--max-frames 200
```

Local video testing verifies the same detection, tracking, and counting pipeline used for live Sage/Waggle camera deployments.

# Plugin Configuration

The plugin exposes the following parameters:

| Parameter | Default | Description |
|---|---|---|
| `camera-source` | `bottom_camera` | Camera name, RTSP stream, or video file |
| `interval` | `1` | Seconds between frame captures |
| `weight` | `/app/models/best.pt` | YOLO model path |
| `confidence` | `0.10` | Detection confidence threshold |
| `imgsz` | `1280` | YOLO inference resolution |
| `roi` | `0.0 0.0 1.0 1.0` | Tracking region |
| `background-subtraction` | `true` | Enable background subtraction |
| `bg-window` | `30` | Background history size |
| `sort-max-age` | `30` | SORT max age |
| `sort-min-hits` | `5` | SORT minimum detections |
| `publish-summary-interval` | `30` | Count publishing interval |
| `max-frames` | `0` | Stop after N frames |

---

# Sage/Waggle Deployment

The bat counter is designed to run continuously as a Sage/Waggle edge plugin.

## Build

```bash
sudo pluginctl build plugin/
```

## Run

For a live Sage/Waggle deployment:

```bash
sudo pluginctl run --name bat-counter <image>
```

The plugin captures thermal imagery, performs bat detection and tracking locally, and publishes count measurements through the Sage platform.

Counts are published using:

```bash
env.count.bat
```

through:

```bash
pywaggle
```

Example measurement:

```bash
env.count.bat = 12
```

These measurements can be collected over repeated nightly runs to create a long-term bat population dataset.

Example workflow:

```bash
Night 1  -> env.count.bat = 12
Night 2  -> env.count.bat = 18
Night 3  -> env.count.bat = 9
          ...
              |
              v
      Nightly Bat Population Trends
```

The edge device only transmits count data rather than full thermal video recordings, reducing bandwidth requirements for field deployments.

# Original Offline Pipeline

Mobile Bat Counter preserves the original offline processing workflow from the research pipeline.

The offline pipeline is useful for:

- Reproducing previous experiments
- Evaluating model performance
- Processing previously recorded thermal videos
- Comparing edge results with offline results

The original workflow:

```bash
Thermal Video Recording
|
v
YAML Configuration
|
v
Background Subtraction
|
v
YOLOv11 Detection
|
v
SORT Tracking
|
v
Annotated Video + CSV Results
```

Run the offline pipeline with:

```bash
pixi run python run_bat_counter.py \
--config configs/generated/PB_noaug_PB_P1.2.2_grey.mov_BGon_ROIon.yaml
```

This workflow remains available for research and validation, while the Sage/Waggle plugin is the primary deployment path.

# Development Environment

Docker and pixi are provided for development and reproducing the original offline environment.

The Sage/Waggle deployment does not require running the offline pixi environment. The production workflow uses the GPU-enabled plugin container built with:

```bash
sudo pluginctl build plugin/
```

---

## Running with Docker

Docker can be used to create a reproducible development environment containing CUDA, PyTorch, YOLO, and computer vision dependencies.

Build the development image:

```bash
docker build -t bat-count-edge .
```

Start the container:

```bash
docker run -it \
  --name bat-count-edge \
  --device=nvidia.com/gpu=0 \
  -v $(pwd):/workspace/mobile-bat-counter \
  bat-count-edge
```

Verify the environment:

```bash
pixi run python -c \
"import torch, ultralytics, cv2; \
print(torch.__version__); \
print(torch.cuda.is_available()); \
print(ultralytics.__version__); \
print(cv2.__version__)"
```

---

## Running Without Docker

Pixi can install and manage the offline research environment directly.

Install dependencies:

```bash
pixi install
```

Run the offline pipeline:

```bash
pixi run python run_bat_counter.py \
--config configs/generated/PB_noaug_PB_P1.2.2_grey.mov_BGon_ROIon.yaml
```

This environment is maintained for offline experimentation and comparison with the edge deployment pipeline.

---

# Performance

The edge pipeline was tested on NVIDIA Thor hardware with GPU-accelerated inference.

Measured performance:

| Metric | Result |
|---|---|
| Device | NVIDIA Thor |
| Architecture | ARM64 |
| Model | YOLOv11n |
| Framework | PyTorch + CUDA |
| GPU acceleration | Enabled |
| Input | Thermal video |
| Inference time | ~30 ms/frame |
| Processing mode | Real-time capable |

Example runtime output:

```text
Model loaded. torch.cuda.is_available()=True
```

frame=100 detections=0 tracked=0 unique=0 infer=29.2ms
frame=200 detections=0 tracked=0 unique=1 infer=29.3ms

Final unique bat count: 1
Saved nightly count: 1 bats -> data/nightly_counts.csv

The validated edge deployment successfully performs:

- GPU-accelerated YOLOv11 inference
- Thermal video processing
- Background subtraction
- SORT tracking
- Unique bat counting
- Nightly count collection
- Sage data publishing

# Model Information

The YOLO model used by BatCount-Edge:

```bash
plugin/models/best.pt
```

is based on the original PB_noaug model from:

https://github.com/Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT

The model was trained for thermal bat detection.

---

# Credits

Original pipeline:

**Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT**

https://github.com/Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT

Adapted for edge deployment as part of the NSF Center for Pandemic Insights project.

---

# Notes

- Large video files are excluded from version control.
- The plugin is optimized for GPU-enabled edge deployment.
- The original offline pipeline remains available for research and comparison.
- The primary output of the edge plugin is bat count data, not annotated video files.