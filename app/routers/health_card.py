import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.health_card import HealthCard
from app.schemas.health_card import HealthCardCreate, HealthCardOut, HealthCardSummary

router = APIRouter(prefix="/health-card", tags=["health-card"])


@router.post("", response_model=HealthCardOut)
def create_or_update_health_card(payload: HealthCardCreate, db: Session = Depends(get_db)):
    card = db.query(HealthCard).filter(HealthCard.device_id == payload.device_id).first()
    if card:
        for field, value in payload.model_dump(exclude={"device_id"}).items():
            setattr(card, field, value)
    else:
        card = HealthCard(**payload.model_dump(), qr_token=secrets.token_urlsafe(16))
        db.add(card)
    db.commit()
    db.refresh(card)
    return HealthCardOut(qr_token=card.qr_token, name=card.name)


@router.get("/qr/{qr_token}", response_model=HealthCardSummary)
def scan_health_card(qr_token: str, db: Session = Depends(get_db)):
    card = db.query(HealthCard).filter(HealthCard.qr_token == qr_token).first()
    if not card:
        raise HTTPException(status_code=404, detail="Health card not found")
    return HealthCardSummary(
        name=card.name,
        emergency_contact=card.emergency_contact,
        allergies=card.allergies,
        conditions=card.conditions,
        blood_group=card.blood_group,
    )
