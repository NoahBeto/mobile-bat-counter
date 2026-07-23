# BatCount-Edge

This project focuses on bringing real-time thermal bat detection and counting to edge computing devices.

The system uses **YOLOv11 (You Only Look Once)** for bat detection and **SORT (Simple Online and Realtime Tracking)** for multi-object tracking. Together, these models detect bats in thermal video, track individual flight trajectories, and estimate the number of unique bats observed during a recording.

The goal of this project is to adapt and optimize an existing thermal-video bat counting pipeline for faster and more efficient deployment on constrained edge hardware. Instead of requiring researchers to collect videos and process them offline, an edge device can automatically analyze thermal camera footage and transmit bat population data.

---

# Credits & Attribution

This project is a continuation of the original repository:

**Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT**  
https://github.com/Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT

The original pipeline was developed for running YOLOv11 + SORT bat counting workflows on HPC systems. This project adapts that workflow for edge computing deployment.

---

# Project Structure

```
mobile-bat-counter/
├── configs/
│   ├── make_configs.sh          # Generates YAML configurations
│   ├── videos.list              # Defines videos and ROIs
│   └── generated/               # Generated model configurations
│
├── models/
│   └── PB_noaug/
│       └── weights/
│           └── best.pt          # YOLOv11 trained weights
│
├── src/
│   ├── tracking.py              # SORT tracking and counting pipeline
│   ├── detection.py             # YOLO bat detection
│   ├── bg_subtract_new.py       # Background subtraction
│   └── utils/
│       └── get_args.py          # Configuration parsing
│
├── sort/
│   └── sort.py                  # SORT tracking algorithm
│
├── examples/
│   ├── sample_annotations/      # Example annotated outputs
│   └── sample_counts.csv        # Example model counts
│
├── videos/                      # Input thermal videos
│
├── pixi.toml                    # Environment dependencies
├── pixi.lock                    # Locked dependency versions
├── Dockerfile                   # Container environment
└── run_bat_counter.py           # Pipeline entry point
```

---

# Pipeline Overview

The BatCount-Edge pipeline processes thermal videos through several stages:

1. **Background subtraction**
   - Removes static environmental features from thermal footage.

2. **YOLOv11 detection**
   - Detects bats in individual video frames using pretrained weights.

3. **SORT tracking**
   - Associates detections between frames to maintain unique bat trajectories.

4. **Counting**
   - Each unique tracked trajectory contributes to the final bat count.

The output includes bat counts and optional annotated videos showing detected and tracked bats.

---

# Edge Computing Deployment

The original workflow required researchers to:

1. Collect thermal camera footage
2. Download recorded videos from deployments
3. Run the detection and tracking pipeline offline
4. Review the resulting bat counts

BatCount-Edge aims to move this processing directly onto an edge device.

A deployed system would:

1. Receive thermal video from a camera
2. Apply background subtraction
3. Run YOLOv11 detection
4. Track bats using SORT
5. Generate nightly population counts
6. Transmit count data instead of raw video

This reduces the amount of data that needs to be transferred from remote deployments while enabling near real-time monitoring.

---

# Running with Docker (Recommended)

Docker provides a reproducible environment containing the required CUDA, PyTorch, YOLO, and computer vision dependencies.

## Clone Repository

```bash
git clone https://github.com/NoahBeto/mobile-bat-counter.git
cd mobile-bat-counter
```

## Build Docker Image

```bash
docker build -t bat-count-edge .
```

## Start Container

```bash
docker run -it \
  --name bat-count-edge \
  --device=nvidia.com/gpu=0 \
  -v $(pwd):/workspace/mobile-bat-counter \
  bat-count-edge
```

## Verify Environment

Inside the container:

```bash
pixi run python -c \
"import torch, ultralytics, cv2; \
print(torch.__version__); \
print(torch.cuda.is_available()); \
print(ultralytics.__version__); \
print(cv2.__version__)"
```

Expected output:

- PyTorch installed: `2.13.0+cu130`
- CUDA available: `True`
- Ultralytics installed: `8.4.104`
- OpenCV installed: `4.10.0`

---

# Running the Bat Counter

Run the pipeline using a generated configuration:

```bash
pixi run python run_bat_counter.py \
--config configs/generated/PB_noaug_PB_P1.2.2_grey.mov_BGon_ROIon.yaml
```

The pipeline performs:

- Thermal video preprocessing
- Background subtraction
- YOLOv11 bat detection
- SORT tracking
- Bat trajectory counting
- Result generation

---

# Running Without Docker

Pixi can also install and manage the environment directly.

## Install Dependencies

```bash
pixi install
```

## Run Pipeline

```bash
pixi run python run_bat_counter.py \
--config configs/generated/PB_noaug_PB_P1.2.2_grey.mov_BGon_ROIon.yaml
```

---

# Configurations and Videos

Videos are configured through:

```
configs/videos.list
```

Format:

```
Site|video_name|x_min y_min x_max y_max
```

Example:

```
CPO|C2.1.1[Val2]_grey.mov|0.0 0.42 1.0 0.52
```

The region of interest (ROI) allows the model to focus on the area where bats are expected to appear.

Generated configurations are stored in:

```
configs/generated/
```

---

# Edge Performance

The pipeline was tested on an NVIDIA Thor edge computing device.

Example benchmark:

| Metric | Result |
|---|---:|
| Device | NVIDIA Thor |
| Input resolution | 640 × 512 |
| Frames processed | 3067 |
| Input FPS | 29.97 |
| Processing FPS | 23.19 |
| CUDA acceleration | Enabled |

The current performance demonstrates that the YOLOv11 + SORT pipeline can run close to real-time on edge hardware.

---

# Reproducibility

The environment is locked using:

```
pixi.toml
pixi.lock
Dockerfile
```

To recreate the environment:

```bash
pixi install
```

or rebuild the Docker image:

```bash
docker build -t bat-count-edge .
```

---

# Notes

Generated videos and annotation outputs are not included in version control due to their large file sizes.

The repository contains the code, configurations, model files, and environment setup required to reproduce the pipeline.
