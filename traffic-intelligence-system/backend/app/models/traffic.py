from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class VideoJob(Base):
    """One uploaded video and its processing history."""
    __tablename__ = "video_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("datasets.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    original_filename: Mapped[str] = mapped_column(String(300))
    input_path: Mapped[str] = mapped_column(String(500))
    output_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|processing|done|failed
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text)
    data_label: Mapped[str] = mapped_column(String(20), default="demo")  # real | dataset | demo
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    line_ratio: Mapped[float] = mapped_column(Float, default=0.6)
    bucket_seconds: Mapped[int] = mapped_column(Integer, default=60)
    frame_stride: Mapped[int] = mapped_column(Integer, default=1)
    fps: Mapped[float | None] = mapped_column(Float)
    total_frames: Mapped[int | None] = mapped_column(Integer)
    duration_s: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VehicleDetection(Base):
    """One row per tracked vehicle (a track = the same vehicle followed across frames)."""
    __tablename__ = "vehicle_detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"), index=True)
    track_id: Mapped[int] = mapped_column(Integer)
    vehicle_type: Mapped[str] = mapped_column(String(20))
    first_frame: Mapped[int] = mapped_column(Integer)
    last_frame: Mapped[int] = mapped_column(Integer)
    avg_confidence: Mapped[float] = mapped_column(Float)
    counted: Mapped[bool] = mapped_column(default=False)  # True if it crossed the counting line


class VehicleCount(Base):
    """Vehicles that crossed the counting line, per time bucket and type."""
    __tablename__ = "vehicle_counts"
    __table_args__ = (Index("ix_counts_loc_time", "location_id", "bucket_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"), index=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vehicle_type: Mapped[str] = mapped_column(String(20))
    count: Mapped[int] = mapped_column(Integer)
    data_label: Mapped[str] = mapped_column(String(20), default="demo")


class TrafficStat(Base):
    """Density and flow per time bucket."""
    __tablename__ = "traffic_stats"
    __table_args__ = (Index("ix_stats_loc_time", "location_id", "bucket_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"), index=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    covered_seconds: Mapped[float] = mapped_column(Float)
    total_count: Mapped[int] = mapped_column(Integer)
    avg_pcu_in_frame: Mapped[float] = mapped_column(Float)
    density_index: Mapped[float] = mapped_column(Float)
    flow_per_min: Mapped[float] = mapped_column(Float)
    data_label: Mapped[str] = mapped_column(String(20), default="demo")


class CongestionRecord(Base):
    __tablename__ = "congestion_records"
    __table_args__ = (Index("ix_cong_loc_time", "location_id", "bucket_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("video_jobs.id", ondelete="CASCADE"), index=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    level: Mapped[str] = mapped_column(String(10))  # low | medium | high
    density_index: Mapped[float] = mapped_column(Float)
    data_label: Mapped[str] = mapped_column(String(20), default="demo")
