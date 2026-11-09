"""Screen and camera capture utilities."""

from __future__ import annotations

import base64
import io
import platform
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

_HAS_CV2 = False
try:
    import cv2

    _HAS_CV2 = True
except ImportError:
    pass


def _resize_if_needed(img: Image.Image, max_dim: int = 1920) -> Image.Image:
    w, h = img.size
    if w <= max_dim and h <= max_dim:
        return img
    ratio = min(max_dim / w, max_dim / h)
    return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)


def image_to_base64(img: Image.Image, fmt: str = "PNG", max_dim: int = 1920) -> str:
    img = _resize_if_needed(img, max_dim)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def capture_screen_macos(region: dict | None = None) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        cmd = ["screencapture", "-x", "-C"]
        if region:
            x, y, w, h = region["x"], region["y"], region["width"], region["height"]
            cmd.extend(["-R", f"{x},{y},{w},{h}"])
        cmd.append(tmp)
        subprocess.run(cmd, check=True, capture_output=True, timeout=10)
        return Image.open(tmp).copy()
    finally:
        Path(tmp).unlink(missing_ok=True)


def capture_screen_linux(region: dict | None = None) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        if region:
            x, y, w, h = region["x"], region["y"], region["width"], region["height"]
            geometry = f"{w}x{h}+{x}+{y}"
            cmd = ["import", "-window", "root", "-crop", geometry, tmp]
        else:
            cmd = ["import", "-window", "root", tmp]
        subprocess.run(cmd, check=True, capture_output=True, timeout=10)
        return Image.open(tmp).copy()
    finally:
        Path(tmp).unlink(missing_ok=True)


def capture_screen(region: dict | None = None) -> Image.Image:
    system = platform.system()
    if system == "Darwin":
        return capture_screen_macos(region)
    elif system == "Linux":
        return capture_screen_linux(region)
    else:
        raise RuntimeError(f"Screen capture not supported on {system}")


def capture_camera(device_index: int = 0) -> Image.Image:
    if not _HAS_CV2:
        raise RuntimeError(
            "opencv-python is required for camera capture. "
            "Install with: pip install eyes-mcp[camera]"
        )
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera device {device_index}")
    try:
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from camera")
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    finally:
        cap.release()


def compute_frame_diff(img_a: Image.Image, img_b: Image.Image) -> float:
    size = (320, 240)
    a = np.array(img_a.convert("L").resize(size), dtype=np.float32)
    b = np.array(img_b.convert("L").resize(size), dtype=np.float32)
    diff = np.abs(a - b)
    return float(np.mean(diff) / 255.0)
