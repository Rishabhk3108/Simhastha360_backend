from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import ROLE_ADMIN, User
from app.models.zone import Zone
from app.schemas.zone import ZoneCreate, ZoneCrowdUpdate, ZoneOut

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=list[ZoneOut])
def list_zones(db: Session = Depends(get_db)):
    return db.query(Zone).all()


@router.post("", response_model=ZoneOut)
def create_zone(
    payload: ZoneCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.patch("/{zone_id}/crowd-level", response_model=ZoneOut)
def set_crowd_level(
    zone_id: int,
    payload: ZoneCrowdUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    zone.crowd_level = payload.crowd_level
    db.commit()
    db.refresh(zone)
    return zone
