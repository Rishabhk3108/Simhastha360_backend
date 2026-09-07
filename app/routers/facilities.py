from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.facility import Facility
from app.models.user import ROLE_ADMIN, User
from app.schemas.facility import FacilityCreate, FacilityOut, FacilityUpdate
from app.services.geo import haversine_km

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilityOut])
def list_facilities(
    type: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Facility).filter(Facility.status == "active")
    if type:
        query = query.filter(Facility.type == type)
    facilities = query.all()

    if lat is not None and lng is not None:
        facilities.sort(key=lambda f: haversine_km(lat, lng, f.lat, f.lng))

    return facilities


@router.post("", response_model=FacilityOut)
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    facility = Facility(**payload.model_dump(), created_by=admin.id)
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


@router.patch("/{facility_id}", response_model=FacilityOut)
def update_facility(
    facility_id: int,
    payload: FacilityUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(facility, field, value)
    db.commit()
    db.refresh(facility)
    return facility


@router.delete("/{facility_id}")
def delete_facility(
    facility_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    facility.status = "removed"
    db.commit()
    return {"ok": True}
