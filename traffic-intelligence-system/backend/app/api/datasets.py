from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database.session import get_db
from app.models import Dataset, Location
from app.schemas.schemas import DatasetCreate, DatasetOut, DatasetUpdate

router = APIRouter(prefix="/datasets", tags=["datasets"], dependencies=[Depends(get_current_user)])


def _check_location(db: Session, location_id: int | None):
    if location_id is not None and not db.get(Location, location_id):
        raise HTTPException(404, "Location not found")


@router.post("", response_model=DatasetOut, status_code=201, dependencies=[Depends(require_admin)])
def add_dataset(body: DatasetCreate, db: Session = Depends(get_db)):
    if db.query(Dataset).filter(Dataset.name == body.name).first():
        raise HTTPException(400, "Dataset name already exists")
    _check_location(db, body.location_id)
    ds = Dataset(**body.model_dump())
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.name).all()


@router.patch("/{dataset_id}", response_model=DatasetOut, dependencies=[Depends(require_admin)])
def update_dataset(dataset_id: int, body: DatasetUpdate, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    data = body.model_dump(exclude_unset=True)
    _check_location(db, data.get("location_id"))
    for k, v in data.items():
        setattr(ds, k, v)
    db.commit()
    db.refresh(ds)
    return ds


@router.delete("/{dataset_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    db.delete(ds)
    db.commit()
