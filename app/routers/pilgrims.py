from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.pilgrim import Guardian, Pilgrim
from app.schemas.pilgrim import (
    GuardianOut,
    PilgrimDetailOut,
    PilgrimLogin,
    PilgrimLoginOut,
    PilgrimRegistration,
    PilgrimRegistrationOut,
    PilgrimSummary,
)

router = APIRouter(prefix="/pilgrims", tags=["pilgrims"])


@router.post("/register", response_model=PilgrimRegistrationOut)
def register(payload: PilgrimRegistration, db: Session = Depends(get_db)):
    """Single endpoint for both entry points (spec: a pilgrim registering
    themselves and naming a guardian, or a guardian registering on behalf of
    a pilgrim) - the resulting record shape is identical either way, only
    `registered_via` tracks which flow was used."""
    guardian = Guardian(**payload.guardian.model_dump())
    db.add(guardian)
    db.flush()

    pilgrim_fields = payload.pilgrim.model_dump(exclude={"password"})
    pilgrim = Pilgrim(
        **pilgrim_fields,
        password_hash=hash_password(payload.pilgrim.password),
        device_id=payload.device_id,
        guardian_id=guardian.id,
        registered_via=payload.registered_via,
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

    return PilgrimRegistrationOut(
        pilgrim_id=pilgrim.id,
        guardian_id=guardian.id,
        name=pilgrim.name,
        registered_via=pilgrim.registered_via,
        created_at=pilgrim.created_at,
    )


@router.post("/login", response_model=PilgrimLoginOut)
def login(payload: PilgrimLogin, db: Session = Depends(get_db)):
    pilgrim = db.query(Pilgrim).filter(Pilgrim.aadhar_number == payload.aadhar_number).first()
    if not pilgrim or not verify_password(payload.password, pilgrim.password_hash):
        raise HTTPException(status_code=401, detail="Invalid Aadhar number or password")

    guardian = pilgrim.guardian
    return PilgrimLoginOut(
        pilgrim_id=pilgrim.id,
        registered_via=pilgrim.registered_via,
        pilgrim=PilgrimDetailOut(
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
        ),
        guardian=GuardianOut(
            name=guardian.name,
            phone=guardian.phone,
            aadhar_number=guardian.aadhar_number,
            email=guardian.email,
            relation_to_pilgrim=guardian.relation_to_pilgrim,
        ),
    )


@router.get("/{pilgrim_id}", response_model=PilgrimSummary)
def get_summary(pilgrim_id: int, db: Session = Depends(get_db)):
    """Lets the app confirm a locally-remembered pilgrim_id still exists
    server-side - a device's local registration flag doesn't auto-clear if
    the backend database is wiped (e.g. during testing) independently."""
    pilgrim = db.query(Pilgrim).filter(Pilgrim.id == pilgrim_id).first()
    if not pilgrim:
        raise HTTPException(status_code=404, detail="Pilgrim not found")
    return PilgrimSummary(pilgrim_id=pilgrim.id, name=pilgrim.name, registered_via=pilgrim.registered_via)
