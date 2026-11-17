"""
YOLOv8 detection + ByteTrack tracking + line-crossing counting.

How it works (simple version):
1. YOLO looks at every frame and draws boxes around vehicles (detection).
2. ByteTrack gives each box an ID and keeps that ID as the vehicle moves (tracking).
3. We draw a virtual horizontal line. When a tracked vehicle's centre crosses it,
   we count that ID ONCE (so the same vehicle is never counted twice).
4. In every frame we also add up how many vehicles are visible (weighted by size, PCU).
   That gives the traffic density.

This module knows nothing about FastAPI or the database. It takes a video file and
returns a VideoResult. app/services/video_processing.py stores that result in PostgreSQL.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

import cv2

from app.core.config import settings

# COCO class id -> our vehicle type. COCO has no auto-rickshaw class (see README).
COCO_TO_TYPE = {2: "car", 3: "bike", 5: "bus", 7: "truck", 1: "other"}  # 1 = bicycle
VEHICLE_CLASS_IDS = list(COCO_TO_TYPE.keys())

# Passenger Car Units: how much road space a vehicle "uses" relative to a car.
# Indicative values in the spirit of Indian (IRC) practice. Change them if you have local guidance.
PCU = {"car": 1.0, "bike": 0.5, "bus": 3.0, "truck": 3.0, "other": 0.3}

# BGR colours for drawing
COLORS = {
    "car": (235, 160, 40),
    "bike": (60, 200, 90),
    "bus": (50, 60, 220),
    "truck": (30, 160, 240),
    "other": (170, 170, 170),
}

_model = None


def get_model():
    """Load YOLO once and reuse it. If the weights file is missing, ultralytics downloads it."""
    global _model
    if _model is None:
        from ultralytics import YOLO

        path = settings.MODEL_PATH
        _model = YOLO(path if os.path.exists(path) else os.path.basename(path))
    return _model


@dataclass
class TrackSummary:
    track_id: int
    vehicle_type: str
    first_frame: int
    last_frame: int
    conf_sum: float = 0.0
    n: int = 0
    counted: bool = False


@dataclass
class Bucket:
    counts: dict = field(default_factory=lambda: defaultdict(int))
    pcu_sum: float = 0.0
    frames: int = 0


@dataclass
class VideoResult:
    fps: float
    total_frames: int
    width: int
    height: int
    duration_s: float
    stride: int
    bucket_seconds: int
    tracks: dict[int, TrackSummary]
    buckets: dict[int, Bucket]
    output_path: str


def _transcode_h264(src: str, dst: str) -> None:
    """OpenCV writes mp4v, which browsers cannot play. ffmpeg converts it to H.264."""
    if shutil.which("ffmpeg"):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vcodec", "libx264",
               "-pix_fmt", "yuv420p", "-preset", "veryfast", "-movflags", "+faststart", dst]
        if subprocess.run(cmd).returncode == 0:
            os.remove(src)
            return
    shutil.move(src, dst)  # fallback: file exists but may not play in the browser


def process_video(
    input_path: str,
    output_path: str,
    line_ratio: float = 0.6,
    stride: int | None = None,
    bucket_seconds: int | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> VideoResult:
    stride = max(1, stride or settings.FRAME_STRIDE)
    bucket_seconds = bucket_seconds or settings.BUCKET_SECONDS

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open the video file (unsupported or corrupt).")
    fps = cap.get(cv2.CAP_PROP_FPS) or settings.DEFAULT_FPS
    if fps <= 1 or fps > 240:
        fps = settings.DEFAULT_FPS
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    line_y = int(height * line_ratio)
    tmp_path = output_path + ".tmp.mp4"
    writer = cv2.VideoWriter(tmp_path, cv2.VideoWriter_fourcc(*"mp4v"), fps / stride, (width, height))

    model = get_model()
    tracks: dict[int, TrackSummary] = {}
    buckets: dict[int, Bucket] = defaultdict(Bucket)
    prev_cy: dict[int, float] = {}
    running = defaultdict(int)  # totals shown on the video overlay

    results = model.track(
        source=input_path, stream=True, persist=True, tracker="bytetrack.yaml",
        classes=VEHICLE_CLASS_IDS, conf=settings.YOLO_CONF, vid_stride=stride, verbose=False,
    )

    frame_i = 0
    for r in results:
        frame = r.orig_img.copy()
        t_s = frame_i * stride / fps
        b = buckets[int(t_s // bucket_seconds)]
        b.frames += 1

        boxes = r.boxes
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().numpy()
            cls = boxes.cls.cpu().numpy().astype(int)
            conf = boxes.conf.cpu().numpy()
            ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else [None] * len(cls)

            for (x1, y1, x2, y2), c, p, tid in zip(xyxy, cls, conf, ids):
                vtype = COCO_TO_TYPE.get(int(c), "other")
                b.pcu_sum += PCU[vtype]
                cy = (y1 + y2) / 2
                if tid is not None:
                    tid = int(tid)
                    tr = tracks.get(tid)
                    if tr is None:
                        tr = tracks[tid] = TrackSummary(tid, vtype, frame_i, frame_i)
                    tr.last_frame = frame_i
                    tr.conf_sum += float(p)
                    tr.n += 1
                    # line crossing: previous and current centre are on opposite sides of the line
                    py = prev_cy.get(tid)
                    if py is not None and not tr.counted and (py - line_y) * (cy - line_y) < 0:
                        tr.counted = True
                        b.counts[tr.vehicle_type] += 1
                        running[tr.vehicle_type] += 1
                    prev_cy[tid] = cy

                color = COLORS[vtype]
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                label = f"{vtype} #{tid}" if tid is not None else vtype
                cv2.putText(frame, f"{label} {p:.2f}", (int(x1), max(15, int(y1) - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # overlay: counting line and running totals
        cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)
        total_counted = sum(running.values())
        cv2.rectangle(frame, (8, 8), (250, 30 + 22 * 5), (0, 0, 0), -1)
        cv2.putText(frame, f"Counted: {total_counted}", (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        for i, t in enumerate(["car", "bike", "bus", "truck"]):
            cv2.putText(frame, f"{t}: {running[t]}", (16, 54 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLORS[t], 2)

        writer.write(frame)
        frame_i += 1
        if on_progress and total and frame_i % 25 == 0:
            on_progress(min(0.99, frame_i * stride / total))

    writer.release()
    _transcode_h264(tmp_path, output_path)

    processed_frames_total = frame_i * stride
    return VideoResult(
        fps=fps, total_frames=processed_frames_total, width=width, height=height,
        duration_s=processed_frames_total / fps, stride=stride, bucket_seconds=bucket_seconds,
        tracks=tracks, buckets=dict(buckets), output_path=output_path,
    )
