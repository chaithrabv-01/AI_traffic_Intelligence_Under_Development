from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

# How honest the data is. Shown as a badge in the dashboard.
CAMERA_SOURCE_TYPES = ("real_cctv", "dataset_footage", "sample", "simulated")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="India")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    # PostGIS point (lon, lat) - used for distance / "nearby" queries
    geom = mapped_column(Geography(geometry_type="POINT", srid=4326))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cameras: Mapped[list["Camera"]] = relationship(back_populates="location", cascade="all, delete-orphan")


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), index=True)
    # real_cctv | dataset_footage | sample | simulated
    source_type: Mapped[str] = mapped_column(String(30), default="sample")
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped[Location] = relationship(back_populates="cameras")
