"""Read-only analytics endpoints used by the dashboard."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import CongestionRecord, TrafficStat
from app.services import traffic_analysis as ta
from app.services.traffic_metrics import congestion_level

router = APIRouter(prefix="/traffic", tags=["traffic"], dependencies=[Depends(get_current_user)])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    return ta.overview(db)


@router.get("/locations")
def locations(start: datetime | None = None, end: datetime | None = None, db: Session = Depends(get_db)):
    return ta.location_summaries(db, start=start, end=end)


@router.get("/compare")
def compare(location_ids: str = Query(..., description="comma separated, e.g. 1,2,3"),
            start: datetime | None = None, end: datetime | None = None, db: Session = Depends(get_db)):
    try:
        ids = [int(x) for x in location_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(400, "location_ids must be integers separated by commas")
    return ta.compare(db, ids, start, end)


@router.get("/peak-hours")
def peak_hours(location_id: int | None = None, start: datetime | None = None,
               end: datetime | None = None, db: Session = Depends(get_db)):
    return ta.peak_hours(db, location_id, start, end)


@router.get("/density-by-hour")
def density_by_hour(location_id: int | None = None, start: datetime | None = None,
                    end: datetime | None = None, db: Session = Depends(get_db)):
    return ta.density_by_hour(db, location_id, start, end)


@router.get("/trends")
def trends(granularity: str = "day", location_id: int | None = None, start: datetime | None = None,
           end: datetime | None = None, db: Session = Depends(get_db)):
    return ta.trends(db, granularity, location_id, start, end)


@router.get("/congestion")
def congestion(location_id: int | None = None, level: str | None = None, limit: int = 200,
               db: Session = Depends(get_db)):
    q = db.query(CongestionRecord)
    if location_id:
        q = q.filter(CongestionRecord.location_id == location_id)
    if level:
        q = q.filter(CongestionRecord.level == level)
    rows = q.order_by(CongestionRecord.bucket_start.desc()).limit(min(limit, 1000)).all()
    return [{"id": r.id, "location_id": r.location_id, "camera_id": r.camera_id, "job_id": r.job_id,
             "bucket_start": r.bucket_start, "level": r.level, "density_index": r.density_index,
             "data_label": r.data_label} for r in rows]


@router.get("/history")
def history(location_id: int | None = None, start: datetime | None = None, end: datetime | None = None,
            limit: int = 200, offset: int = 0, db: Session = Depends(get_db)):
    q = db.query(TrafficStat)
    if location_id:
        q = q.filter(TrafficStat.location_id == location_id)
    q = ta._apply_range(q, TrafficStat.bucket_start, start, end)
    rows = q.order_by(TrafficStat.bucket_start.desc()).offset(offset).limit(min(limit, 1000)).all()
    return [{"id": r.id, "location_id": r.location_id, "camera_id": r.camera_id, "job_id": r.job_id,
             "bucket_start": r.bucket_start, "total_count": r.total_count, "density_index": r.density_index,
             "flow_per_min": r.flow_per_min, "covered_seconds": r.covered_seconds,
             "level": congestion_level(r.density_index), "data_label": r.data_label} for r in rows]
