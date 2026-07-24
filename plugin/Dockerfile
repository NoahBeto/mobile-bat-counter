# Sage/Waggle Bat Counting Plugin — Dockerfile
# Base: NVIDIA PyTorch 25.08 — CUDA 13.0, Blackwell sm_110 kernels (works on Thor).
# Reference: sage-waggle skill templates/ml-plugin-Dockerfile
#
# Build (on a Thor / arm64 node):
#   sudo pluginctl build .
#   sudo pluginctl run --name bat-counter-test <image> -- --camera-source "rtsp://..."

FROM nvcr.io/nvidia/pytorch:25.08-py3

WORKDIR /app

# --- requirements (freeze base-image stack so pip can't swap Blackwell kernels) ---
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    TORCH_VER=$(python3 -c "import torch; print(torch.__version__)") && \
    TV_VER=$(python3 -c "import torchvision; print(torchvision.__version__)") && \
    NP_VER=$(python3 -c "import numpy; print(numpy.__version__)") && \
    echo "Freezing base-image stack: torch==${TORCH_VER} torchvision==${TV_VER} numpy==${NP_VER}" && \
    printf "torch==${TORCH_VER}\ntorchvision==${TV_VER}\nnumpy==${NP_VER}\n" > /tmp/constraints.txt && \
    pip install --no-cache-dir -c /tmp/constraints.txt -r requirements.txt

# Fix OpenCV: the base image ships opencv compiled against a different numpy.
RUN pip uninstall -y opencv-python opencv-python-headless 2>/dev/null; \
    rm -rf /usr/local/lib/python3.*/dist-packages/cv2* && \
    pip install --no-cache-dir -c /tmp/constraints.txt opencv-python-headless>=4.8.0

# --- pre-bake model weights (edge nodes may not have internet) ---
# Copy the pretrained bat model into the image at a known path.
# The .pt file is ~5.4 MB so this is a cheap layer.
#
# Build context is plugin/, so the weights file lives at plugin/models/best.pt
# (copied from models/PB_noaug/weights/best.pt, which is outside the build
# context). See plugin/.gitignore: plugin/models/ is ignored.
COPY models/best.pt /app/models/best.pt
ENV BAT_MODEL=/app/models/best.pt

# --- pre-bake sample thermal videos for testing ---
# Copied from videos/ at the repo root (outside the build context).
# See plugin/.gitignore: plugin/videos/ is ignored.
# WORKDIR is /app, so "videos/P1.1.2_grey.mov" resolves to /app/videos/...
COPY videos/ /app/videos/

# --- copy the plugin code + SORT shim + the upstream sort.py it exec()s ---
# app.py uses sort_shim which exec()s the real sort/sort.py. Build context is
# plugin/, so sort.py is vendored at plugin/sort/sort.py (gitignored).
COPY app.py /app/app.py
COPY sort_shim.py /app/sort_shim.py
COPY sort/sort.py /app/sort/sort.py

# offline mode: prevent any runtime model downloads (weights are baked in)
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

ENTRYPOINT ["python3", "/app/app.py"]
