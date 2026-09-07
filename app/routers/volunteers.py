from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, hash_password, require_roles
from app.models.user import (
    ROLE_ADMIN,
    ROLE_VOLUNTEER,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    User,
    VolunteerProfile,
)
from app.schemas.volunteer import (
    VolunteerApply,
    VolunteerAvailabilityUpdate,
    VolunteerOut,
    VolunteerReviewAction,
)

router = APIRouter(prefix="/volunteers", tags=["volunteers"])


def _to_out(profile: VolunteerProfile) -> VolunteerOut:
    return VolunteerOut(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.user.name,
        phone=profile.user.phone,
        skills=profile.skills,
        status=profile.status,
        on_duty=profile.on_duty,
        preferred_zone_id=profile.preferred_zone_id,
        created_at=profile.created_at,
    )


@router.post("/apply", response_model=VolunteerOut)
def apply(payload: VolunteerApply, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=ROLE_VOLUNTEER,
        language=payload.language,
    )
    db.add(user)
    db.flush()

    profile = VolunteerProfile(
        user_id=user.id,
        age=payload.age,
        city_state=payload.city_state,
        skills=",".join(payload.skills),
        availability_dates=payload.availability_dates or "",
        preferred_zone_id=payload.preferred_zone_id,
        id_proof_url=payload.id_proof_url,
        status=STATUS_PENDING,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _to_out(profile)


@router.get("/me", response_model=VolunteerOut)
def my_status(db: Session = Depends(get_db), user: User = Depends(require_roles(ROLE_VOLUNTEER))):
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == user.id).first()
    return _to_out(profile)


@router.patch("/me/availability", response_model=VolunteerOut)
def update_my_availability(
    payload: VolunteerAvailabilityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(ROLE_VOLUNTEER)),
):
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == user.id).first()
    if profile.status != STATUS_APPROVED:
        raise HTTPException(status_code=403, detail="Not yet approved")
    profile.on_duty = payload.on_duty
    db.commit()
    db.refresh(profile)
    return _to_out(profile)


@router.get("", response_model=list[VolunteerOut])
def list_volunteers(
    status: str | None = None,
    skill: str | None = None,
    zone_id: int | None = None,
    on_duty: bool | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    query = db.query(VolunteerProfile)
    if status:
        query = query.filter(VolunteerProfile.status == status)
    if zone_id is not None:
        query = query.filter(VolunteerProfile.preferred_zone_id == zone_id)
    if on_duty is not None:
        query = query.filter(VolunteerProfile.on_duty == on_duty)
    profiles = query.all()
    if skill:
        profiles = [p for p in profiles if skill in p.skills.split(",")]
    return [_to_out(p) for p in profiles]


@router.patch("/{profile_id}/review", response_model=VolunteerOut)
def review_volunteer(
    profile_id: int,
    payload: VolunteerReviewAction,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Volunteer application not found")

    if payload.action == "approve":
        profile.status = STATUS_APPROVED
    elif payload.action == "reject":
        profile.status = STATUS_REJECTED
    elif payload.action == "request_info":
        pass  # status stays pending; note is surfaced to the volunteer out-of-band (notification)
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

    db.commit()
    db.refresh(profile)
    return _to_out(profile)
