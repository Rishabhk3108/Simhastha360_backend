import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.pilgrim import Pilgrim
from app.schemas.pilgrim import (
    ForeignerLogin,
    ForeignerRegistration,
    GuardianOut,
    PilgrimDetailOut,
    PilgrimLinkTokenOut,
    PilgrimLocationUpdate,
    PilgrimLogin,
    PilgrimLoginOut,
    PilgrimRegistration,
    PilgrimRegistrationOut,
    PilgrimSummary,
)

router = APIRouter(prefix="/pilgrims", tags=["pilgrims"])

LINK_TOKEN_TTL_MINUTES = 15


def _detail_out(pilgrim: Pilgrim) -> PilgrimDetailOut:
    return PilgrimDetailOut(
        name=pilgrim.name,
        phone=pilgrim.phone,
        aadhar_number=pilgrim.aadhar_number,
        age=pilgrim.age,
        photo_base64=pilgrim.photo_base64,
        samagra_id=pilgrim.samagra_id,
        address_line1=pilgrim.address_line1,
        address_line2=pilgrim.address_line2,
        city=pilgrim.city,
        state=pilgrim.state,
        pincode=pilgrim.pincode,
        country=pilgrim.country,
        medical_history=pilgrim.medical_history,
        is_foreigner=pilgrim.is_foreigner,
    )


@router.post("/register", response_model=PilgrimRegistrationOut)
def register(payload: PilgrimRegistration, db: Session = Depends(get_db)):
    pilgrim_fields = payload.pilgrim.model_dump(exclude={"password"})
    pilgrim = Pilgrim(
        **pilgrim_fields,
        password_hash=hash_password(payload.pilgrim.password),
        device_id=payload.device_id,
    )
    db.add(pilgrim)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this Aadhar number already exists. Please sign in instead.",
        )
    db.refresh(pilgrim)

    return PilgrimRegistrationOut(pilgrim_id=pilgrim.id, name=pilgrim.name, created_at=pilgrim.created_at)


@router.post("/register-foreign", response_model=PilgrimRegistrationOut)
def register_foreign(payload: ForeignerRegistration, db: Session = Depends(get_db)):
    existing = db.query(Pilgrim).filter(Pilgrim.phone == payload.foreigner.phone, Pilgrim.is_foreigner.is_(True)).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this phone number already exists. Please sign in instead.")

    pilgrim = Pilgrim(
        device_id=payload.device_id,
        name=payload.foreigner.name,
        phone=payload.foreigner.phone,
        country=payload.foreigner.country,
        photo_base64=payload.foreigner.photo_base64,
        password_hash=hash_password(payload.foreigner.password),
        is_foreigner=True,
    )
    db.add(pilgrim)
    db.commit()
    db.refresh(pilgrim)

    return PilgrimRegistrationOut(pilgrim_id=pilgrim.id, name=pilgrim.name, created_at=pilgrim.created_at)


@router.post("/login-foreign", response_model=PilgrimLoginOut)
def login_foreign(payload: ForeignerLogin, db: Session = Depends(get_db)):
    pilgrim = db.query(Pilgrim).filter(Pilgrim.phone == payload.phone, Pilgrim.is_foreigner.is_(True)).first()
    if not pilgrim or not verify_password(payload.password, pilgrim.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone number or password")

    return PilgrimLoginOut(
        pilgrim_id=pilgrim.id,
        pilgrim=_detail_out(pilgrim),
        guardian=None,
    )


@router.post("/login", response_model=PilgrimLoginOut)
def login(payload: PilgrimLogin, db: Session = Depends(get_db)):
    pilgrim = db.query(Pilgrim).filter(Pilgrim.aadhar_number == payload.aadhar_number).first()
    if not pilgrim or not verify_password(payload.password, pilgrim.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Aadhar number or password")

    # Old registration flow only - a pilgrim registered under the current
    # flow simply has no guardian row (guardian_id is None).
    guardian = pilgrim.guardian
    return PilgrimLoginOut(
        pilgrim_id=pilgrim.id,
        pilgrim=_detail_out(pilgrim),
        guardian=GuardianOut(
            name=guardian.name,
            phone=guardian.phone,
            aadhar_number=guardian.aadhar_number,
            email=guardian.email,
            relation_to_pilgrim=guardian.relation_to_pilgrim,
        )
        if guardian
        else None,
    )


@router.get("/{pilgrim_id}", response_model=PilgrimSummary)
def get_summary(pilgrim_id: int, db: Session = Depends(get_db)):
    """Lets the app confirm a locally-remembered pilgrim_id still exists
    server-side - a device's local registration flag doesn't auto-clear if
    the backend database is wiped (e.g. during testing) independently."""
    pilgrim = db.query(Pilgrim).filter(Pilgrim.id == pilgrim_id).first()
    if not pilgrim:
        raise HTTPException(status_code=404, detail="Pilgrim not found")
    return PilgrimSummary(pilgrim_id=pilgrim.id, name=pilgrim.name)


@router.post("/{pilgrim_id}/link-token", response_model=PilgrimLinkTokenOut)
def create_link_token(pilgrim_id: int, db: Session = Depends(get_db)):
    """Generates a short-lived, single-use code the pilgrim shows as a QR -
    a guardian scanning it (see /guardians/me/link) is how the two get
    linked. Short and uppercase so it also works as a manually-typed
    fallback, not just a scanned code."""
    pilgrim = db.query(Pilgrim).filter(Pilgrim.id == pilgrim_id).first()
    if not pilgrim:
        raise HTTPException(status_code=404, detail="Pilgrim not found")
    token = secrets.token_hex(4).upper()
    pilgrim.link_token = token
    pilgrim.link_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=LINK_TOKEN_TTL_MINUTES)
    db.commit()
    return PilgrimLinkTokenOut(token=token, expires_at=pilgrim.link_token_expires_at)


@router.patch("/{pilgrim_id}/location")
def update_pilgrim_location(pilgrim_id: int, payload: PilgrimLocationUpdate, db: Session = Depends(get_db)):
    pilgrim = (
        db.query(Pilgrim).filter(Pilgrim.id == pilgrim_id, Pilgrim.device_id == payload.device_id).first()
    )
    if not pilgrim:
        raise HTTPException(status_code=404, detail="Pilgrim not found")
    pilgrim.last_lat = payload.lat
    pilgrim.last_lng = payload.lng
    pilgrim.location_updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}
