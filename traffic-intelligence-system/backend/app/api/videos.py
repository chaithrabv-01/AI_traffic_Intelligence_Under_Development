"""Upload videos, start AI processing, read results."""
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.database.session import get_db
from app.models import Camera, Dataset, TrafficStat, User, VehicleCount, VideoJob
from app.schemas.schemas import RegisterLocalVideo, VideoJobOut
from app.services.traffic_metrics import congestion_level, data_label_for
from app.services.video_processing import run_job

router = APIRouter(prefix="/videos", tags=["videos"], dependencies=[Depends(get_current_user)])
ALLOWED_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def _out(job: VideoJob) -> VideoJobOut:
    o = VideoJobOut.model_validate(job)
    o.has_output = bool(job.output_path and os.path.exists(job.output_path))
    return o


def _validate_source(db: Session, camera_id: int, dataset_id: int | None) -> tuple[Camera, Dataset | None]:
    """The honesty rule: never tie footage to a real place the source does not support."""
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    ds = db.get(Dataset, dataset_id) if dataset_id else None
    if dataset_id and not ds:
        raise HTTPException(404, "Dataset not found")
    if ds and cam.source_type in ("real_cctv", "dataset_footage"):
        if ds.location_id is None:
            raise HTTPException(400, "This dataset has no verified location. Use a camera whose source type is "
                                     "'sample' or 'simulated', or set the dataset's verified location first.")
        if ds.location_id != cam.location_id:
            raise HTTPException(400, "The dataset's verified location differs from the camera's location.")
    return cam, ds


def _create_job(db, cam, ds, user, filename, path, recorded_at, line_ratio) -> VideoJob:
    job = VideoJob(
        camera_id=cam.id, dataset_id=ds.id if ds else None, created_by=user.id,
        original_filename=filename, input_path=path, status="queued",
        data_label=data_label_for(cam.source_type),
        recorded_at=recorded_at or datetime.now(timezone.utc), line_ratio=line_ratio,
        bucket_seconds=settings.BUCKET_SECONDS, frame_stride=settings.FRAME_STRIDE,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.post("/upload", response_model=VideoJobOut, status_code=202)
async def upload_video(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: int = Form(...),
    dataset_id: int | None = Form(None),
    recorded_at: datetime | None = Form(None),
    line_ratio: float = Form(0.6),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type. Use one of: {', '.join(sorted(ALLOWED_EXT))}")
    if not 0.1 <= line_ratio <= 0.9:
        raise HTTPException(400, "line_ratio must be between 0.1 and 0.9")
    cam, ds = _validate_source(db, camera_id, dataset_id)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    size, limit = 0, settings.MAX_UPLOAD_MB * 1024 * 1024
    with open(path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                f.close()
                os.remove(path)
                raise HTTPException(413, f"File is larger than {settings.MAX_UPLOAD_MB} MB")
            f.write(chunk)

    job = _create_job(db, cam, ds, user, file.filename, path, recorded_at, line_ratio)
    background.add_task(run_job, job.id)
    return _out(job)


@router.post("/register-local", response_model=VideoJobOut, status_code=202)
def register_local(body: RegisterLocalVideo, background: BackgroundTasks,
                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Process a video already placed in datasets/raw_videos (best for big dataset files)."""
    root = os.path.realpath(settings.UPLOAD_DIR)
    path = os.path.realpath(os.path.join(root, body.relative_path))
    if not path.startswith(root + os.sep):
        raise HTTPException(400, "Path must stay inside datasets/raw_videos")
    if not os.path.isfile(path):
        raise HTTPException(404, "File not found in datasets/raw_videos")
    cam, ds = _validate_source(db, body.camera_id, body.dataset_id)
    job = _create_job(db, cam, ds, user, os.path.basename(path), path, body.recorded_at, body.line_ratio)
    background.add_task(run_job, job.id)
    return _out(job)


@router.get("", response_model=list[VideoJobOut])
def list_jobs(camera_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(VideoJob)
    if camera_id:
        q = q.filter(VideoJob.camera_id == camera_id)
    return [_out(j) for j in q.order_by(VideoJob.id.desc()).limit(200).all()]


@router.get("/{job_id}", response_model=VideoJobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(VideoJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _out(job)


@router.get("/{job_id}/results")
def job_results(job_id: int, db: Session = Depends(get_db)):
    job = db.get(VideoJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    by_type = dict(db.query(VehicleCount.vehicle_type, func.sum(VehicleCount.count))
                   .filter(VehicleCount.job_id == job_id).group_by(VehicleCount.vehicle_type).all())
    timeline = [{"bucket_start": s.bucket_start, "total_count": s.total_count, "density_index": s.density_index,
                 "flow_per_min": s.flow_per_min, "level": congestion_level(s.density_index)}
                for s in db.query(TrafficStat).filter(TrafficStat.job_id == job_id)
                .order_by(TrafficStat.bucket_start).all()]
    by_type = {k: int(v) for k, v in by_type.items()}
    return {"job": _out(job), "total_vehicles": sum(by_type.values()), "by_type": by_type, "timeline": timeline}


@router.get("/{job_id}/video")
def job_video(job_id: int, db: Session = Depends(get_db)):
    job = db.get(VideoJob, job_id)
    if not job or not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(404, "Processed video not available")
    return FileResponse(job.output_path, media_type="video/mp4")


@router.post("/{job_id}/reprocess", response_model=VideoJobOut, status_code=202, dependencies=[Depends(require_admin)])
def reprocess(job_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    job = db.get(VideoJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status == "processing":
        raise HTTPException(409, "Job is already processing")
    job.status, job.progress = "queued", 0.0
    db.commit()
    background.add_task(run_job, job.id)
    return _out(job)


@router.delete("/{job_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(VideoJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.output_path and os.path.exists(job.output_path):
        os.remove(job.output_path)
    db.delete(job)  # DB rows for counts/stats are removed by ON DELETE CASCADE
    db.commit()
