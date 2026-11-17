"""Pydantic schemas: the shapes of request bodies and responses."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SourceType = Literal["real_cctv", "dataset_footage", "sample", "simulated"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- auth ----
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=72)


class UserOut(ORM):
    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- locations / cameras ----
class LocationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    city: str
    state: str | None = None
    country: str = "India"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class LocationOut(ORM):
    id: int
    name: str
    city: str
    state: str | None
    country: str
    latitude: float
    longitude: float


class CameraCreate(BaseModel):
    camera_code: str = Field(min_length=2, max_length=60)
    name: str
    location_id: int
    source_type: SourceType = "sample"
    description: str | None = None


class CameraOut(ORM):
    id: int
    camera_code: str
    name: str
    location_id: int
    source_type: str
    description: str | None


# ---- datasets ----
class DatasetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    source_url: str | None = None
    license: str | None = None
    data_type: Literal["video", "images", "csv"] = "video"
    is_real_footage: bool = True
    source_location_note: str | None = Field(default=None, description="Where it was really recorded")
    location_id: int | None = Field(default=None, description="Only if the source supports this location")
    local_path: str | None = None
    notes: str | None = None


class DatasetUpdate(BaseModel):
    source_url: str | None = None
    license: str | None = None
    source_location_note: str | None = None
    location_id: int | None = None
    local_path: str | None = None
    notes: str | None = None


class DatasetOut(ORM):
    id: int
    name: str
    source_url: str | None
    license: str | None
    data_type: str
    is_real_footage: bool
    source_location_note: str | None
    location_id: int | None
    local_path: str | None
    notes: str | None
    created_at: datetime


# ---- video jobs ----
class RegisterLocalVideo(BaseModel):
    relative_path: str = Field(description="Path inside datasets/raw_videos, e.g. ua_detrac/MVI_20011.mp4")
    camera_id: int
    dataset_id: int | None = None
    recorded_at: datetime | None = None
    line_ratio: float = Field(default=0.6, ge=0.1, le=0.9)


class VideoJobOut(ORM):
    id: int
    camera_id: int
    dataset_id: int | None
    original_filename: str
    status: str
    progress: float
    error: str | None
    data_label: str
    recorded_at: datetime
    line_ratio: float
    fps: float | None
    total_frames: int | None
    duration_s: float | None
    created_at: datetime
    finished_at: datetime | None
    has_output: bool = False
