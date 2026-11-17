"""
The formulas for density and congestion live here, in one place, so they are easy to change.

density_index  = average PCU visible per frame in the time bucket
                 = (sum over frames of sum of PCU weights of vehicles in that frame) / number of frames
flow_per_min   = vehicles that crossed the counting line / minutes of video in the bucket

Congestion level (from density_index):
    <= DENSITY_LOW_MAX      -> low
    <= DENSITY_MEDIUM_MAX   -> medium
    otherwise               -> high

IMPORTANT: this is an image-based density measure for ONE camera view. It is not speed, not
travel time and not real-time city traffic. Thresholds depend on how wide the camera view is,
so tune DENSITY_*_MAX for each camera.
"""
from app.core.config import settings


def density_index(pcu_sum: float, frames: int) -> float:
    return round(pcu_sum / frames, 2) if frames else 0.0


def flow_per_min(total_count: int, covered_seconds: float) -> float:
    return round(total_count / (covered_seconds / 60), 2) if covered_seconds > 0 else 0.0


def congestion_level(density: float) -> str:
    if density <= settings.DENSITY_LOW_MAX:
        return "low"
    if density <= settings.DENSITY_MEDIUM_MAX:
        return "medium"
    return "high"


def data_label_for(source_type: str) -> str:
    """real_cctv -> 'real', dataset_footage -> 'dataset', sample/simulated -> 'demo'."""
    return {"real_cctv": "real", "dataset_footage": "dataset"}.get(source_type, "demo")
