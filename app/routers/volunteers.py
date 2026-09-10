from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, require_roles
from app.models.user import (
    ROLE_ADMIN,
    ROLE_VOLUNTEER,
    ROLE_VOLUNTEER_MANAGER,
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

# Day-to-day volunteer approval/oversight belongs to the police/municipal
# volunteer managers; the main admin role is kept as an override rather than
# cut out of the loop entirely.
MANAGES_VOLUNTEERS = (ROLE_ADMIN, ROLE_VOLUNTEER_MANAGER)


def _to_out(profile: VolunteerProfile) -> VolunteerOut:
    return VolunteerOut(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.user.name,
        phone=profile.user.phone,
        age=profile.age,
        gender=profile.gender,
        email=profile.email,
        city_state=profile.city_state,
        permanent_address=profile.permanent_address,
        emergency_contact_name=profile.emergency_contact_name,
        emergency_contact_phone=profile.emergency_contact_phone,
        id_proof_type=profile.id_proof_type,
        id_number=profile.id_number,
        id_proof_front_doc_id=profile.id_proof_front_doc_id,
        id_proof_back_doc_id=profile.id_proof_back_doc_id,
        photo_doc_id=profile.photo_doc_id,
        skills=profile.skills,
        languages=profile.languages,
        availability_slots=profile.availability_slots or [],
        prior_experience=profile.prior_experience,
        tshirt_size=profile.tshirt_size,
        organization_affiliation=profile.organization_affiliation,
        medical_conditions=profile.medical_conditions,
        no_criminal_record=profile.no_criminal_record,
        code_of_conduct_accepted=profile.code_of_conduct_accepted,
        media_consent=profile.media_consent,
        status=profile.status,
        review_note=profile.review_note,
        rating=profile.rating,
        on_duty=profile.on_duty,
        accepts_emergencies=profile.accepts_emergencies,
        preferred_zone_id=profile.preferred_zone_id,
        current_lat=profile.user.current_lat,
        current_lng=profile.user.current_lng,
        location_updated_at=profile.user.location_updated_at,
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
        gender=payload.gender,
        email=payload.email,
        city_state=payload.city_state,
        permanent_address=payload.permanent_address,
        emergency_contact_name=payload.emergency_contact_name,
        emergency_contact_phone=payload.emergency_contact_phone,
        id_proof_type=payload.id_proof_type,
        id_number=payload.id_number,
        id_proof_front_doc_id=payload.id_proof_front_doc_id,
        id_proof_back_doc_id=payload.id_proof_back_doc_id,
        photo_doc_id=payload.photo_doc_id,
        skills=",".join(payload.skills),
        languages=",".join(payload.languages),
        availability_slots=[slot.model_dump() for slot in payload.availability_slots],
        prior_experience=payload.prior_experience,
        tshirt_size=payload.tshirt_size,
        organization_affiliation=payload.organization_affiliation,
        medical_conditions=payload.medical_conditions,
        no_criminal_record=payload.no_criminal_record,
        code_of_conduct_accepted=payload.code_of_conduct_accepted,
        media_consent=payload.media_consent,
        preferred_zone_id=payload.preferred_zone_id,
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
    if payload.on_duty is not None:
        profile.on_duty = payload.on_duty
    if payload.accepts_emergencies is not None:
        profile.accepts_emergencies = payload.accepts_emergencies
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
    manager: User = Depends(require_roles(*MANAGES_VOLUNTEERS)),
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
    manager: User = Depends(require_roles(*MANAGES_VOLUNTEERS)),
):
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Volunteer application not found")

    if payload.action == "approve":
        profile.status = STATUS_APPROVED
        profile.review_note = payload.note
        if payload.rating is not None:
            profile.rating = payload.rating
    elif payload.action == "reject":
        profile.status = STATUS_REJECTED
        profile.review_note = payload.note
    elif payload.action == "request_info":
        profile.review_note = payload.note  # status stays pending; surfaced to the volunteer at login
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

    db.commit()
    db.refresh(profile)
    return _to_out(profile)
