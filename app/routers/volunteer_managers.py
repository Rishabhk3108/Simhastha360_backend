from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, require_roles
from app.models.user import ROLE_ADMIN, ROLE_VOLUNTEER_MANAGER, User

router = APIRouter(prefix="/volunteer-managers", tags=["volunteer-managers"])


class VolunteerManagerCreate(BaseModel):
    name: str
    phone: str
    password: str


class VolunteerManagerOut(BaseModel):
    id: int
    name: str
    phone: str

    class Config:
        from_attributes = True


# No self-registration for this role, by design - accounts are created
# directly by the main admin for police/municipal staff.
@router.post("", response_model=VolunteerManagerOut)
def create_volunteer_manager(
    payload: VolunteerManagerCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")
    user = User(
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=ROLE_VOLUNTEER_MANAGER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[VolunteerManagerOut])
def list_volunteer_managers(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    return db.query(User).filter(User.role == ROLE_VOLUNTEER_MANAGER).all()
