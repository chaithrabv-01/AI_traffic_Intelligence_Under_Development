"""SQL queries behind the /traffic endpoints. Everything is computed from stored rows (no fake data)."""
from datetime import datetime

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CongestionRecord, Location, TrafficStat, VehicleCount


def _local(col):
    """Convert a timestamp column to the configured local timezone before grouping by hour/day."""
    return func.timezone(settings.TIMEZONE, col)


def _apply_range(q, col, start: datetime | None, end: datetime | None):
    if start:
        q = q.filter(col >= start)
    if end:
        q = q.filter(col <= end)
    return q


def totals_by_type(db: Session, location_ids=None, start=None, end=None) -> dict[str, int]:
    q = db.query(VehicleCount.vehicle_type, func.sum(VehicleCount.count))
    if location_ids:
        q = q.filter(VehicleCount.location_id.in_(location_ids))
    q = _apply_range(q, VehicleCount.bucket_start, start, end)
    return {t: int(n) for t, n in q.group_by(VehicleCount.vehicle_type).all()}


def location_summaries(db: Session, location_ids=None, start=None, end=None) -> list[dict]:
    locs = db.query(Location)
    if location_ids:
        locs = locs.filter(Location.id.in_(location_ids))
    out = []
    for loc in locs.order_by(Location.name).all():
        by_type = totals_by_type(db, [loc.id], start, end)

        sq = db.query(func.avg(TrafficStat.density_index), func.avg(TrafficStat.flow_per_min),
                      func.array_agg(func.distinct(TrafficStat.data_label))).filter(TrafficStat.location_id == loc.id)
        avg_density, avg_flow, labels = _apply_range(sq, TrafficStat.bucket_start, start, end).one()

        cq = db.query(CongestionRecord).filter(CongestionRecord.location_id == loc.id)
        cq = _apply_range(cq, CongestionRecord.bucket_start, start, end)
        latest = cq.order_by(CongestionRecord.bucket_start.desc()).first()
        n_rec = cq.count()
        n_high = cq.filter(CongestionRecord.level == "high").count()

        out.append({
            "location_id": loc.id, "name": loc.name, "city": loc.city, "state": loc.state,
            "latitude": loc.latitude, "longitude": loc.longitude,
            "total_vehicles": sum(by_type.values()), "by_type": by_type,
            "avg_density": round(float(avg_density), 2) if avg_density is not None else None,
            "avg_flow_per_min": round(float(avg_flow), 2) if avg_flow is not None else None,
            "latest_level": latest.level if latest else None,
            "latest_density": latest.density_index if latest else None,
            "latest_time": latest.bucket_start if latest else None,
            "pct_high": round(100 * n_high / n_rec, 1) if n_rec else 0.0,
            "data_labels": sorted(l for l in (labels or []) if l),
        })
    return out


def overview(db: Session) -> dict:
    summaries = location_summaries(db)
    with_data = [s for s in summaries if s["latest_level"]]
    alerts = [s for s in with_data if s["latest_level"] == "high"]
    densities = [s["latest_density"] for s in with_data if s["latest_density"] is not None]
    by_type = totals_by_type(db)
    return {
        "total_vehicles": sum(by_type.values()),
        "by_type": by_type,
        "locations_total": len(summaries),
        "active_locations": len(with_data),
        "current_density": round(sum(densities) / len(densities), 2) if densities else None,
        "alerts": [{"location_id": a["location_id"], "name": a["name"], "density": a["latest_density"],
                    "time": a["latest_time"], "data_labels": a["data_labels"]} for a in alerts],
        "locations": summaries,
    }


def peak_hours(db: Session, location_id=None, start=None, end=None) -> list[dict]:
    hour = extract("hour", _local(VehicleCount.bucket_start)).label("hour")
    q = db.query(hour, func.sum(VehicleCount.count))
    if location_id:
        q = q.filter(VehicleCount.location_id == location_id)
    q = _apply_range(q, VehicleCount.bucket_start, start, end)
    rows = {int(h): int(n) for h, n in q.group_by(hour).all()}
    return [{"hour": h, "vehicles": rows.get(h, 0)} for h in range(24)]


def density_by_hour(db: Session, location_id=None, start=None, end=None) -> list[dict]:
    hour = extract("hour", _local(TrafficStat.bucket_start)).label("hour")
    q = db.query(hour, func.avg(TrafficStat.density_index))
    if location_id:
        q = q.filter(TrafficStat.location_id == location_id)
    q = _apply_range(q, TrafficStat.bucket_start, start, end)
    rows = {int(h): round(float(d), 2) for h, d in q.group_by(hour).all()}
    return [{"hour": h, "density": rows.get(h)} for h in range(24)]


def trends(db: Session, granularity="day", location_id=None, start=None, end=None) -> list[dict]:
    if granularity not in ("hour", "day", "week"):
        granularity = "day"
    period = func.date_trunc(granularity, _local(VehicleCount.bucket_start)).label("period")
    q = db.query(period, func.sum(VehicleCount.count))
    if location_id:
        q = q.filter(VehicleCount.location_id == location_id)
    q = _apply_range(q, VehicleCount.bucket_start, start, end)
    return [{"period": p, "vehicles": int(n)} for p, n in q.group_by(period).order_by(period).all()]


def compare(db: Session, location_ids: list[int], start=None, end=None) -> list[dict]:
    summaries = location_summaries(db, location_ids, start, end)
    for s in summaries:
        hours = peak_hours(db, s["location_id"], start, end)
        busiest = max(hours, key=lambda h: h["vehicles"])
        s["peak_hour"] = busiest["hour"] if busiest["vehicles"] > 0 else None
    return summaries
