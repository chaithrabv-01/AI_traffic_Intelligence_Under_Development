from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2 import WKTElement
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database.session import get_db
from app.models import Camera, Location
from app.schemas.schemas import CameraCreate, CameraOut, LocationCreate, LocationOut

router = APIRouter(tags=["locations"], dependencies=[Depends(get_current_user)])


@router.post("/locations", response_model=LocationOut, status_code=201, dependencies=[Depends(require_admin)])
def add_location(body: LocationCreate, db: Session = Depends(get_db)):
    if db.query(Location).filter(Location.name == body.name).first():
        raise HTTPException(400, "A location with this name already exists")
    loc = Location(**body.model_dump(),
                   geom=WKTElement(f"POINT({body.longitude} {body.latitude})", srid=4326))
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.get("/locations", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db)):
    return db.query(Location).order_by(Location.name).all()


@router.get("/locations/nearby", response_model=list[LocationOut])
def nearby(lat: float, lon: float, radius_km: float = 25, db: Session = Depends(get_db)):
    """PostGIS query: locations within radius_km of a point."""
    point = func.ST_GeogFromText(f"SRID=4326;POINT({lon} {lat})")
    return db.query(Location).filter(func.ST_DWithin(Location.geom, point, radius_km * 1000)).all()


@router.get("/locations/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(404, "Location not found")
    return loc


@router.delete("/locations/{location_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(404, "Location not found")
    db.delete(loc)
    db.commit()


@router.post("/cameras", response_model=CameraOut, status_code=201, dependencies=[Depends(require_admin)])
def add_camera(body: CameraCreate, db: Session = Depends(get_db)):
    if not db.get(Location, body.location_id):
        raise HTTPException(404, "Location not found")
    if db.query(Camera).filter(Camera.camera_code == body.camera_code).first():
        raise HTTPException(400, "Camera code already exists")
    cam = Camera(**body.model_dump())
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam


@router.get("/cameras", response_model=list[CameraOut])
def list_cameras(location_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Camera)
    if location_id:
        q = q.filter(Camera.location_id == location_id)
    return q.order_by(Camera.camera_code).all()
