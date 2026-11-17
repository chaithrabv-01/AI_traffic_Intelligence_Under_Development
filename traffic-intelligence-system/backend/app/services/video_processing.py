"""Runs the AI on a VideoJob and saves the results to PostgreSQL. Called as a background task."""
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ai.detector import process_video
from app.core.config import settings
from app.database.session import SessionLocal
from app.models import (
    Camera, CongestionRecord, TrafficStat, VehicleCount, VehicleDetection, VideoJob,
)
from app.services import traffic_metrics as tm


def _clear_old_results(db: Session, job_id: int) -> None:
    for model in (VehicleDetection, VehicleCount, TrafficStat, CongestionRecord):
        db.query(model).filter(model.job_id == job_id).delete()


def run_job(job_id: int) -> None:
    """Entry point used by BackgroundTasks. Creates its own DB session (the request's is closed)."""
    db = SessionLocal()
    try:
        job = db.get(VideoJob, job_id)
        if job is None:
            return
        camera = db.get(Camera, job.camera_id)
        job.status = "processing"
        job.progress = 0.0
        job.error = None
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        _clear_old_results(db, job.id)

        os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
        out_path = os.path.join(settings.PROCESSED_DIR, f"job_{job.id}.mp4")

        def on_progress(p: float) -> None:
            job.progress = round(p, 3)
            db.commit()

        result = process_video(
            job.input_path, out_path, line_ratio=job.line_ratio,
            stride=job.frame_stride, bucket_seconds=job.bucket_seconds, on_progress=on_progress,
        )

        # 1) one row per tracked vehicle
        for tr in result.tracks.values():
            db.add(VehicleDetection(
                job_id=job.id, track_id=tr.track_id, vehicle_type=tr.vehicle_type,
                first_frame=tr.first_frame, last_frame=tr.last_frame,
                avg_confidence=round(tr.conf_sum / tr.n, 3) if tr.n else 0.0, counted=tr.counted,
            ))

        # 2) per time bucket: counts, density/flow stats, congestion level
        for idx, b in sorted(result.buckets.items()):
            start = job.recorded_at + timedelta(seconds=idx * job.bucket_seconds)
            covered = b.frames * result.stride / result.fps
            total = sum(b.counts.values())
            dens = tm.density_index(b.pcu_sum, b.frames)
            for vtype, n in b.counts.items():
                db.add(VehicleCount(job_id=job.id, camera_id=camera.id, location_id=camera.location_id,
                                    bucket_start=start, vehicle_type=vtype, count=n, data_label=job.data_label))
            db.add(TrafficStat(job_id=job.id, camera_id=camera.id, location_id=camera.location_id,
                               bucket_start=start, covered_seconds=round(covered, 2), total_count=total,
                               avg_pcu_in_frame=dens, density_index=dens,
                               flow_per_min=tm.flow_per_min(total, covered), data_label=job.data_label))
            db.add(CongestionRecord(job_id=job.id, camera_id=camera.id, location_id=camera.location_id,
                                    bucket_start=start, level=tm.congestion_level(dens),
                                    density_index=dens, data_label=job.data_label))

        job.output_path = out_path
        job.fps = result.fps
        job.total_frames = result.total_frames
        job.duration_s = result.duration_s
        job.status = "done"
        job.progress = 1.0
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:  # store the error so the dashboard can show it
        db.rollback()
        job = db.get(VideoJob, job_id)
        if job:
            job.status = "failed"
            job.error = str(exc)[:2000]
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
