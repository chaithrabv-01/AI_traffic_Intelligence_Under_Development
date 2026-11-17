"""Importing every model here makes sure SQLAlchemy / Alembic know about all tables."""
from app.models.dataset import Dataset  # noqa: F401
from app.models.location import Camera, Location  # noqa: F401
from app.models.traffic import (  # noqa: F401
    CongestionRecord,
    TrafficStat,
    VehicleCount,
    VehicleDetection,
    VideoJob,
)
from app.models.user import User  # noqa: F401
