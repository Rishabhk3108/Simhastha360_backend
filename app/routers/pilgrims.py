from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.pilgrim import Guardian, Pilgrim
from app.schemas.pilgrim import PilgrimRegistration, PilgrimRegistrationOut, PilgrimSummary

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

    pilgrim = Pilgrim(
        **payload.pilgrim.model_dump(),
        device_id=payload.device_id,
        guardian_id=guardian.id,
        registered_via=payload.registered_via,
    )
    db.add(pilgrim)
    db.commit()
    db.refresh(pilgrim)

    return PilgrimRegistrationOut(
        pilgrim_id=pilgrim.id,
        guardian_id=guardian.id,
        name=pilgrim.name,
        registered_via=pilgrim.registered_via,
        created_at=pilgrim.created_at,
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
