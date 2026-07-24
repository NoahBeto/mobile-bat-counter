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

Mobile-Bat-Counter moves this processing directly onto an edge device.

The deployed system can:

1. Receive thermal camera footage
2. Perform background subtraction
3. Run YOLOv11 bat detection
4. Track bats using SORT
5. Generate population counts
6. Transmit count data instead of raw video

This reduces data transfer requirements and enables near real-time monitoring of bat populations.

---

# Pipeline

```bash
Thermal Camera / Video File
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
```

---

# Project Structure

```bash
mobile-bat-counter/

├── plugin/
│ ├── app.py # Real-time edge plugin
│ ├── Dockerfile # GPU container definition
│ ├── requirements.txt # Plugin dependencies
│ ├── sage.yaml # Sage/Waggle deployment configuration
│ ├── sort/
│ │ └── sort.py # SORT tracker
│ ├── sort_shim.py # Lightweight SORT dependency shim
│ └── models/
│ └── best.pt # YOLOv11 weights
│
├── src/
│ ├── tracking.py # Original offline tracking pipeline
│ ├── detection.py # YOLO detection utilities
│ └── bg_subtract_new.py # Background subtraction
│
├── configs/
│ ├── videos.list # Video and ROI definitions
│ └── generated/ # Generated YAML configs
│
├── models/
│ └── PB_noaug/
│ └── weights/
│ └── best.pt # Original YOLO weights
│
├── sort/
│ └── sort.py
│
├── videos/ # Sample thermal videos
│
├── run_bat_counter.py # Offline pipeline entry point
├── pixi.toml # Offline environment
├── pixi.lock
└── README.md
```

---

# Edge Deployment (Primary Workflow)

The edge plugin runs inside an NVIDIA GPU-enabled container.

The tested deployment environment:

- Hardware: NVIDIA Thor
- Architecture: ARM64
- CUDA acceleration: Enabled
- GPU inference: PyTorch + YOLOv11

---

# Build the Plugin

From the repository root:

```bash
sudo pluginctl build plugin/
```

This creates the plugin container image:

```bash
10.31.81.1:5000/local/plugin
```

# Test with a Sample Thermal Video

Run the container directly with GPU access:

```bash
podman run --rm -it \
  --name <container-name> \
  --device=nvidia.com/gpu=<gpu-id> \
  <plugin-image> \
  --camera-source <video-or-camera-source> \
  --max-frames <number-of-frames> \
  --interval <seconds-between-frames>
```

Example: 

```bash
podman run --rm -it \
  --name bat-counter \
  --device=nvidia.com/gpu=0 \
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
```

A successful run confirms:

- NVIDIA GPU access
- CUDA-enabled PyTorch
- YOLOv11 inference
- Background subtraction
- SORT tracking
- Bat counting

# Camera Sources

The plugin supports three input types.

## 1. Sage/Waggle Camera

Production deployments use WES camera names:

```bash
--camera-source bottom_camera
```

The node resolves the camera stream automatically.

## 2. RTSP Camera

Network thermal cameras can be used directly:

```bash
--camera-source rtsp://camera-address/stream
```

Example:

```bash
sudo pluginctl run --name bat-counter <image> -- \
--camera-source rtsp://user:password@camera-ip:554/stream
```

## 3. Local Video File

For testing:

```bash
--camera-source videos/P1.1.2_grey.mov
```

Use:

```bash
--max-frames <number-of-frames>
```

to limit processing.

Example:

```bash
--max-frames 200
```

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

For deployment through Sage tools:

## Build

```bash
sudo pluginctl build plugin/
```

## Run

```bash
sudo pluginctl run --name bat-counter <image>
```

The plugin publishes bat counts through:

```bash
env.count.bat
```

using:

```bash
pywaggle
```

The resulting measurements can be accessed through the Sage data platform.

# Original Offline Pipeline
Mobile Bat Counter preserves the original offline processing workflow.

The original pipeline:

- Processes recorded thermal videos
- Uses YAML configurations
- Runs YOLOv11 detection
- Uses SORT tracking
- Generates annotated videos and CSV counts

Run with:

```bash
pixi run python run_bat_counter.py \
--config configs/generated/PB_noaug_PB_P1.2.2_grey.mov_BGon_ROIon.yaml
```

# Offline Environment Setup

Install dependencies:

```bash
pixi install
```

Run:

```bash
pixi run python run_bat_counter.py \
--config configs/generated/PB_noaug_PB_P1.2.2_grey.mov_BGon_ROIon.yaml
```

# Performance

The pipeline was tested on NVIDIA Thor edge hardware.

Example performance:

| Metric | Result |
|---|---|
| Device | NVIDIA Thor |
| Model | YOLOv11n |
| CUDA acceleration | Enabled |
| Input | Thermal video |
| Inference time | ~30 ms/frame |
| Processing mode | Real-time capable |

The plugin successfully performs GPU-accelerated inference and bat counting directly on edge hardware.

---

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

---

# Verified Edge Deployment Workflow

The tested deployment workflow is:

## Build the plugin

```bash
sudo pluginctl build plugin/
```

## Run with GPU acceleration

```bash
podman run --rm -it \
  --name bat-counter \
  --device=nvidia.com/gpu=0 \
  10.31.81.1:5000/local/plugin \
  --camera-source videos/P1.1.2_grey.mov \
  --max-frames 200 \
  --interval 0
```

This verifies:

- NVIDIA GPU access
- CUDA-enabled PyTorch
- YOLOv11 inference
- Background subtraction
- SORT tracking
- Bat counting

This workflow represents the current validated BatCount-Edge deployment path.