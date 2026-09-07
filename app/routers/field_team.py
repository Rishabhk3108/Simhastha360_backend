from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, require_roles
from app.models.user import ROLE_ADMIN, ROLE_FIELD_TEAM, ROLE_VOLUNTEER, User

router = APIRouter(prefix="/field-team", tags=["field-team"])


class FieldTeamCreate(BaseModel):
    name: str
    phone: str
    password: str
    language: str = "en"


class FieldTeamOut(BaseModel):
    id: int
    name: str
    phone: str
    current_lat: float | None
    current_lng: float | None
    location_updated_at: datetime | None

    class Config:
        from_attributes = True


class LocationUpdate(BaseModel):
    lat: float
    lng: float


@router.post("", response_model=FieldTeamOut)
def create_field_team_member(
    payload: FieldTeamCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    user = User(
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=ROLE_FIELD_TEAM,
        language=payload.language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[FieldTeamOut])
def list_field_team(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    return db.query(User).filter(User.role == ROLE_FIELD_TEAM).all()


@router.patch("/me/location", response_model=FieldTeamOut)
def update_my_location(
    payload: LocationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(ROLE_FIELD_TEAM, ROLE_VOLUNTEER)),
):
    user.current_lat = payload.lat
    user.current_lng = payload.lng
    user.location_updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
