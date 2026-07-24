# bat-counter-yolov11-sort — Sage/Waggle edge plugin

Thermal-video bat detection and tracking using **YOLO11 + SORT**, adapted from the
[Bat-Counting-YOLOv11-SORT](https://github.com/Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT)
project for edge deployment on Sage/Waggle nodes (NVIDIA Thor, ARM64 + CUDA).

## What it does

Captures frames from a camera, runs YOLO11 detection on the GPU to find "hot bat"
thermal signatures, tracks them across frames with SORT, counts unique track IDs,
and publishes the bat count to the Sage data API via pywaggle.

```
camera stream (WES-named / RTSP / file)
      │
      v
frame sampling (interval-based)
      │
      v
[optional] inline background subtraction
      │
      v
YOLO detection (GPU, default imgsz=1280)
      │
      v
ROI filtering (tracking region)
      │
      v
SORT tracking
      │
      v
unique bat count
      │
      v
pywaggle publish → env.count.bat
      │
      v
Sage data API / Beehive
```

## Files

- `app.py` — main plugin: camera capture loop, YOLO + SORT, pywaggle publish
- `sort_shim.py` — stubs out `skimage`/`matplotlib` so `sort/sort.py` loads without dev deps
- `Dockerfile` — builds on `nvcr.io/nvidia/pytorch:25.08-py3` (Blackwell sm_110, baked weights)
- `requirements.txt` — slim runtime deps (pywaggle, ultralytics, opencv-headless, filterpy, lap)
- `sage.yaml` — ECR metadata + configurable inputs

## Camera sources

The `--camera-source` argument accepts three kinds of source (checked in order):

1. **WES-named camera** (e.g. `bottom_camera`) — resolves via the node's WES data config. This is the default and the intended production source on a real Sage node.
2. **RTSP URL** (e.g. `rtsp://user:pass@ip:554/h264Preview_01_main`) — passes directly to `cv2.VideoCapture`. Good for testing with IP cameras outside a WES node.
3. **Local file path** (e.g. `videos/P1.1.2_grey.mov`) — for local testing against a sample video. Use `--max-frames N` to stop after N frames.

## Build and run with pluginctl (on a Thor node)

```bash
cd /path/to/Bat-Counting-YOLOv11-SORT

# build the plugin image (the Dockerfile is at plugin/, but pluginctl builds from a dir)
sudo pluginctl build plugin/

# run with a WES-named camera (default)
sudo pluginctl run --name bat-test <image> -- --camera-source bottom_camera --interval 1

# run with an RTSP camera
sudo pluginctl run --name bat-test <image> -- \
    --camera-source "rtsp://admin:PASSWORD@192.168.1.100:554/h264Preview_01_sub" --interval 2

# local test on a sample video (no GPU publish, logs to stdout)
sudo pluginctl run --name bat-test <image> -- \
    --camera-source videos/P1.1.2_grey.mov --max-frames 200 --interval 0

# inspect
sudo pluginctl logs bat-test
sudo pluginctl ps

# cleanup before re-running
sudo pluginctl rm bat-test
```

## Local testing without a cluster

The plugin runs outside a Sage node too (without pywaggle available). In that mode
it logs the would-be-published count to stdout instead of calling `plugin.publish()`:

```bash
python3 plugin/app.py --camera-source videos/P1.1.2_grey.mov --max-frames 100 --interval 0
```

Set `PYWAGGLE_LOG_DIR=/tmp/wlog` to exercise the real publish path locally and inspect
`/tmp/wlog/data.ndjson`.

## Configuration

All inputs are also exposed via `sage.yaml` for ECR/sesctl deployment. Float-valued
args are declared as `string` (ECR validation rejects `float` and `boolean` types) and
parsed numerically at runtime.

| Input | Default | Description |
| --- | --- | --- |
| `camera-source` | `bottom_camera` | WES camera name, RTSP URL, or file path |
| `interval` | `1` | Seconds between frame captures |
| `weight` | `/app/models/best.pt` | Path to the YOLO model weights (baked in) |
| `confidence` | `"0.10"` | Detection confidence threshold |
| `imgsz` | `1280` | YOLO inference image size (lower = faster) |
| `roi` | `"0.0 0.0 1.0 1.0"` | Tracking ROI: `x0 y0 x1 y1` normalized 0-1 |
| `amplification` | `"1.0"` | Pixel amplification before inference |
| `background-subtraction` | `"true"` | Enable inline per-frame bg subtraction |
| `bg-window` | `30` | Background subtraction sliding window size |
| `sort-max-age` | `30` | SORT `max_age` |
| `sort-min-hits` | `5` | SORT `min_hits` |
| `sort-iou-threshold` | `"0.10"` | SORT IoU threshold |
| `publish-summary-interval` | `30` | Publish a summary count every N frames |
| `max-frames` | `0` | Stop after N frames (0 = continuous forever) |

## What changed from the original pipeline

This edge port is **additive** — the original `src/`, `configs/`, and `run_bat_counter.py`
are untouched and still work for HPC/offline runs.

Differences:
- Continuous camera capture instead of whole-video processing
- GPU inference (`.to("cuda")`) instead of the original `.to("cpu")` spot
- No SLURM / no full-video transcode; background subtraction is optional and inline per-frame
- No annotated video output by default; the primary output is a published count
- pywaggle `plugin.publish("env.count.bat", count, …)` so data reaches Beehive/data API
- Slim `requirements.txt` (cut `ipdb`, `ruff`, `ipython`, `matplotlib`, `scikit-image`)
