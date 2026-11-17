from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    source_url: Mapped[str | None] = mapped_column(String(500))
    license: Mapped[str | None] = mapped_column(String(200))
    data_type: Mapped[str] = mapped_column(String(30), default="video")  # video | images | csv
    is_real_footage: Mapped[bool] = mapped_column(default=True)
    # Where the dataset was REALLY recorded, in words (e.g. "Beijing and Tianjin, China").
    source_location_note: Mapped[str | None] = mapped_column(Text)
    # Only set when the dataset's source supports this location. Otherwise leave empty.
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"))
    local_path: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
