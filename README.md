# mobile-bat-counter

Real-time thermal bat detection and counting on the edge using YOLOv11 + SORT tracking, adapted for deployment on Sage/Waggle nodes (NVIDIA Thor, ARM64 + CUDA).

This project is a fork of the original [Bat-Counting-YOLOv11-SORT](https://github.com/Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT) by Sarah Lagattuta.

## Two-Track System

This repo contains two independent pipelines that share detection and tracking logic but serve different use cases:

### 1. Batch Track (Offline Analysis)

```
src/           — core detection, tracking, and background subtraction modules
configs/       — YAML configs that specify video files, model weights, and pipeline params
run_bat_counter.py — CLI wrapper that runs src.tracking with a config file
```

This is the original pipeline from the upstream fork. It reads `.mov` thermal video files, runs two-pass background subtraction (median of all frames), YOLO detection, SORT tracking, and writes annotated videos + CSV counts. This is designed for offline analysis on an HPC cluster or a server with a folder of recorded videos.

The batch track is untouched from the original repo and still works as-is:

```bash
python run_bat_counter.py --config configs/generated/PB_noaug_PB_P1.1.2_grey.mov_BGon_ROIon.yaml
```

### 2. Plugin Track (Real-time Edge Deployment)

```
plugin/
  app.py        — main plugin: capture loop, YOLO + SORT, pywaggle publish
  Dockerfile    — builds on nvcr.io/nvidia/pytorch:25.08-py3 (Blackwell sm_110 kernels)
  sage.yaml     — ECR metadata + configurable inputs for Sage deployment
  sort_shim.py  — stubs skimage/matplotlib so sort.py loads without dev deps
  sort/sort.py  — vendored SORT tracker
  models/best.pt — baked-in YOLO weights (gitignored, copied at build time)
  requirements.txt — slim runtime deps
  overview.md   — detailed plugin documentation
```

This is the Sage/Waggle edge plugin. It lives in a container on a Thor node, captures frames from a live camera (WES-named, RTSP, or local file for testing), runs inline background subtraction + GPU inference + SORT tracking, and publishes unique bat counts to the Sage data API via pywaggle (`env.count.bat`). It does not write CSVs or annotated videos — the primary output is a published message.

**Build and run on a Thor node:**

```bash
# build the container image
sudo pluginctl build plugin/

# run with the WES bottom camera (default production source)
sudo pluginctl run --name bat-counter <image>

# run with an RTSP thermal camera
sudo pluginctl run --name bat-counter <image> -- \
    --camera-source "rtsp://user:pass@192.168.1.100:554/stream"

# local test on a sample video (logs to stdout, no publish)
sudo pluginctl run --name bat-counter <image> -- \
    --camera-source videos/P1.1.2_grey.mov --max-frames 200 --interval 0
```

For full plugin configuration options and local testing instructions, see [plugin/overview.md](plugin/overview.md).

## Model Weights

The baked-in weights (`plugin/models/best.pt`) are copied from `models/PB_noaug/weights/best.pt`. This is the PB_noaug model — the same variant referenced by the config names and sample counts in `examples/sample_counts.csv`.

## Environment

- **GPU inference:** requires the NVIDIA PyTorch container (`nvcr.io/nvidia/pytorch:25.08-py3`) which includes Blackwell `sm_110` kernels. The host Pixi environment cannot run GPU inference on Thor (conda-forge PyTorch lacks sm_110 kernels for aarch64).
- **CPU testing:** works via Pixi locally with `CUDA_VISIBLE_DEVICES=""` — useful for verifying logic, not for real deployment.
- **Dependencies:** see `plugin/requirements.txt` for the plugin track and `pixi.toml` / `requirements.txt` for the batch track.

## Credits & Attribution

Core detection and tracking logic adapted from [Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT](https://github.com/Sarah-Lagattuta/Bat-Counting-YOLOv11-SORT).

Funding: NSF Center for Pandemic Insights.
