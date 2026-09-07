from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.incident import LOST_MATCHED, SOS_PENDING, SOS_RESOLVED, SOS_RESPONDING, LostPersonReport, SOSAlert
from app.models.user import ROLE_ADMIN, ROLE_FIELD_TEAM, ROLE_VOLUNTEER, User
from app.models.user import VolunteerProfile
from app.schemas.incident import LostPersonCreate, LostPersonOut, SOSCreate, SOSOut
from app.services.geo import haversine_km

router = APIRouter(tags=["incidents"])


def _find_nearest_responder(db: Session, lat: float, lng: float) -> User | None:
    field_team = db.query(User).filter(User.role == ROLE_FIELD_TEAM, User.current_lat.isnot(None)).all()
    candidates = [(u, haversine_km(lat, lng, u.current_lat, u.current_lng)) for u in field_team]

    on_duty_volunteers = (
        db.query(User)
        .join(VolunteerProfile, VolunteerProfile.user_id == User.id)
        .filter(VolunteerProfile.on_duty.is_(True), User.current_lat.isnot(None))
        .all()
    )
    candidates += [(u, haversine_km(lat, lng, u.current_lat, u.current_lng)) for u in on_duty_volunteers]

    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[1])
    return candidates[0][0]


@router.post("/sos", response_model=SOSOut)
def create_sos(payload: SOSCreate, db: Session = Depends(get_db)):
    responder = _find_nearest_responder(db, payload.lat, payload.lng)
    sos = SOSAlert(
        **payload.model_dump(),
        status=SOS_RESPONDING if responder else SOS_PENDING,
        assigned_responder_id=responder.id if responder else None,
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)
    return sos


@router.get("/sos", response_model=list[SOSOut])
def list_sos(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    return db.query(SOSAlert).order_by(SOSAlert.created_at.desc()).all()


@router.patch("/sos/{sos_id}/resolve", response_model=SOSOut)
def resolve_sos(
    sos_id: int,
    db: Session = Depends(get_db),
    responder: User = Depends(require_roles(ROLE_ADMIN, ROLE_FIELD_TEAM, ROLE_VOLUNTEER)),
):
    sos = db.query(SOSAlert).filter(SOSAlert.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")
    sos.status = SOS_RESOLVED
    sos.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sos)
    return sos


@router.post("/lost-person", response_model=LostPersonOut)
def report_lost_person(payload: LostPersonCreate, db: Session = Depends(get_db)):
    report = LostPersonReport(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/lost-person", response_model=list[LostPersonOut])
def list_lost_person_reports(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    return db.query(LostPersonReport).order_by(LostPersonReport.created_at.desc()).all()


@router.post("/lost-person/{report_id}/confirm-match", response_model=LostPersonOut)
def confirm_lost_person_match(
    report_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    """Marks a match confirmed by a human help-desk operator. Deliberately no automated
    face-matching against surveillance feeds - similarity search (when added) only runs
    within the voluntarily-submitted photo pool, and a human always confirms here."""
    report = db.query(LostPersonReport).filter(LostPersonReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Lost person report not found")
    report.status = LOST_MATCHED
    db.commit()
    db.refresh(report)
    return report
