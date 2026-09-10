from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, require_roles
from app.models.incident import SOS_RESOLVED, SOSAlert
from app.models.pilgrim import GuardianLink, Pilgrim
from app.models.user import ROLE_GUARDIAN, User
from app.models.zone import Zone
from app.schemas.guardian import GuardianAccountOut, GuardianRegister, LinkedPilgrimOut, LinkPilgrimRequest
from app.services.geo import haversine_km

router = APIRouter(prefix="/guardians", tags=["guardians"])


@router.post("/register", response_model=GuardianAccountOut)
def register_guardian(payload: GuardianRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    user = User(
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=ROLE_GUARDIAN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _linked_pilgrim_out(db: Session, pilgrim: Pilgrim) -> LinkedPilgrimOut:
    zone_name = None
    crowd_level = None
    if pilgrim.last_lat is not None and pilgrim.last_lng is not None:
        zones = db.query(Zone).all()
        if zones:
            nearest = min(zones, key=lambda z: haversine_km(pilgrim.last_lat, pilgrim.last_lng, z.center_lat, z.center_lng))
            zone_name = nearest.name
            crowd_level = nearest.crowd_level

    has_active_sos = (
        db.query(SOSAlert)
        .filter(SOSAlert.device_id == pilgrim.device_id, SOSAlert.status != SOS_RESOLVED)
        .first()
        is not None
    )

    return LinkedPilgrimOut(
        pilgrim_id=pilgrim.id,
        name=pilgrim.name,
        age=pilgrim.age,
        photo_base64=pilgrim.photo_base64,
        last_lat=pilgrim.last_lat,
        last_lng=pilgrim.last_lng,
        location_updated_at=pilgrim.location_updated_at,
        zone_name=zone_name,
        crowd_level=crowd_level,
        has_active_sos=has_active_sos,
    )


@router.post("/me/link", response_model=LinkedPilgrimOut)
def link_pilgrim(
    payload: LinkPilgrimRequest,
    db: Session = Depends(get_db),
    guardian: User = Depends(require_roles(ROLE_GUARDIAN)),
):
    pilgrim = db.query(Pilgrim).filter(Pilgrim.link_token == payload.token).first()
    if (
        not pilgrim
        or not pilgrim.link_token_expires_at
        or pilgrim.link_token_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=400, detail="This code is invalid or has expired - ask them to generate a new one")

    existing = (
        db.query(GuardianLink)
        .filter(GuardianLink.guardian_user_id == guardian.id, GuardianLink.pilgrim_id == pilgrim.id)
        .first()
    )
    if not existing:
        db.add(GuardianLink(guardian_user_id=guardian.id, pilgrim_id=pilgrim.id))

    # Single-use - consumed whether or not this guardian was already linked,
    # so a scanned/shared code can't be reused later.
    pilgrim.link_token = None
    pilgrim.link_token_expires_at = None
    db.commit()
    db.refresh(pilgrim)
    return _linked_pilgrim_out(db, pilgrim)


@router.get("/me/pilgrims", response_model=list[LinkedPilgrimOut])
def my_pilgrims(
    db: Session = Depends(get_db),
    guardian: User = Depends(require_roles(ROLE_GUARDIAN)),
):
    links = db.query(GuardianLink).filter(GuardianLink.guardian_user_id == guardian.id).all()
    pilgrim_ids = [link.pilgrim_id for link in links]
    if not pilgrim_ids:
        return []
    pilgrims = db.query(Pilgrim).filter(Pilgrim.id.in_(pilgrim_ids)).all()
    return [_linked_pilgrim_out(db, p) for p in pilgrims]
