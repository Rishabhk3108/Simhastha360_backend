from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.incident import (
    LOST_MATCHED,
    SOS_ACK_TIMEOUT_SECONDS,
    SOS_ASSIGNED,
    SOS_PENDING,
    SOS_RESOLVED,
    SOS_RESPONDING,
    LostPersonReport,
    SOSAlert,
)
from app.models.pilgrim import GuardianLink, Pilgrim
from app.models.user import ROLE_ADMIN, ROLE_FIELD_TEAM, ROLE_VOLUNTEER, ROLE_VOLUNTEER_MANAGER, User
from app.models.user import VolunteerProfile
from app.schemas.incident import LostPersonCreate, LostPersonOut, SOSCreate, SOSOut, SOSReassign, SOSStatusOut
from app.services.geo import haversine_km
from app.services.mappls import RouteUnavailable, get_driving_route
from app.services.notifications import notify

router = APIRouter(tags=["incidents"])

# Same split as tasks/reports: volunteer managers run this day-to-day, admin
# kept as an override.
MANAGES_SOS = (ROLE_ADMIN, ROLE_VOLUNTEER_MANAGER)


def _find_nearest_responder(db: Session, lat: float, lng: float, exclude_ids: set[int]) -> User | None:
    field_query = db.query(User).filter(User.role == ROLE_FIELD_TEAM, User.current_lat.isnot(None))
    if exclude_ids:
        field_query = field_query.filter(User.id.notin_(exclude_ids))
    candidates = [(u, haversine_km(lat, lng, u.current_lat, u.current_lng)) for u in field_query.all()]

    # Only volunteers who've explicitly opted into emergency response (a
    # separate switch from the general on-duty toggle) are ever paged for an
    # SOS - being available for routine tasks doesn't imply consenting to be
    # woken up for a medical emergency.
    volunteer_query = (
        db.query(User)
        .join(VolunteerProfile, VolunteerProfile.user_id == User.id)
        .filter(
            VolunteerProfile.on_duty.is_(True),
            VolunteerProfile.accepts_emergencies.is_(True),
            User.current_lat.isnot(None),
        )
    )
    if exclude_ids:
        volunteer_query = volunteer_query.filter(User.id.notin_(exclude_ids))
    candidates += [(u, haversine_km(lat, lng, u.current_lat, u.current_lng)) for u in volunteer_query.all()]

    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[1])
    return candidates[0][0]


def _assign(db: Session, sos: SOSAlert, responder: User) -> None:
    sos.assigned_responder_id = responder.id
    sos.assigned_at = datetime.now(timezone.utc)
    sos.status = SOS_ASSIGNED
    db.commit()
    notify(
        db,
        responder,
        "Emergency SOS nearby - respond now",
        "A pilgrim near you needs help. Open the app to acknowledge and get directions.",
        {"type": "sos_assigned", "sos_id": sos.id},
    )


def _maybe_escalate(db: Session, sos: SOSAlert) -> None:
    """If an assigned responder hasn't acknowledged within the timeout, try
    the next-nearest eligible responder instead. No decline action exists for
    responders by design - silence is the only thing that reassigns."""
    if sos.status != SOS_ASSIGNED or not sos.assigned_at:
        return
    # The DB column is naive (no tz), but every write here uses UTC - reattach
    # it before subtracting from an aware "now", or Python raises a TypeError.
    assigned_at = sos.assigned_at.replace(tzinfo=timezone.utc) if sos.assigned_at.tzinfo is None else sos.assigned_at
    elapsed = (datetime.now(timezone.utc) - assigned_at).total_seconds()
    if elapsed < SOS_ACK_TIMEOUT_SECONDS:
        return

    tried = set(sos.tried_responder_ids or [])
    if sos.assigned_responder_id:
        tried.add(sos.assigned_responder_id)
    sos.tried_responder_ids = list(tried)
    sos.escalated = True

    next_responder = _find_nearest_responder(db, sos.lat, sos.lng, exclude_ids=tried)
    if next_responder:
        _assign(db, sos, next_responder)
    else:
        sos.status = SOS_PENDING
        sos.assigned_responder_id = None
        db.commit()


def _notify_guardians(db: Session, device_id: str) -> None:
    """A guardian watching over this pilgrim (linked via QR code) should
    never find out about an SOS late - notify every linked guardian
    immediately, independent of responder assignment."""
    pilgrim = db.query(Pilgrim).filter(Pilgrim.device_id == device_id).first()
    if not pilgrim:
        return
    links = db.query(GuardianLink).filter(GuardianLink.pilgrim_id == pilgrim.id).all()
    for link in links:
        guardian = db.query(User).filter(User.id == link.guardian_user_id).first()
        if guardian:
            notify(
                db,
                guardian,
                "Emergency alert",
                f"{pilgrim.name} has sent an SOS. Open the app for the latest status.",
                {"type": "sos_guardian_alert", "pilgrim_id": pilgrim.id},
            )


@router.post("/sos", response_model=SOSOut)
def create_sos(payload: SOSCreate, db: Session = Depends(get_db)):
    responder = _find_nearest_responder(db, payload.lat, payload.lng, exclude_ids=set())
    sos = SOSAlert(**payload.model_dump(), status=SOS_PENDING)
    db.add(sos)
    db.commit()
    db.refresh(sos)
    if responder:
        _assign(db, sos, responder)
        db.refresh(sos)
    _notify_guardians(db, payload.device_id)
    return sos


@router.get("/sos", response_model=list[SOSOut])
def list_sos(
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_SOS)),
):
    alerts = db.query(SOSAlert).filter(SOSAlert.status != SOS_RESOLVED).all()
    for sos in alerts:
        _maybe_escalate(db, sos)
    return db.query(SOSAlert).order_by(SOSAlert.created_at.desc()).all()


@router.get("/sos/assigned-to-me", response_model=SOSOut | None)
def get_sos_assigned_to_me(
    db: Session = Depends(get_db),
    responder: User = Depends(require_roles(ROLE_FIELD_TEAM, ROLE_VOLUNTEER)),
):
    """Polled by a responder's own app to detect a newly-assigned emergency -
    there is deliberately no decline action, only this + acknowledge."""
    sos = (
        db.query(SOSAlert)
        .filter(SOSAlert.assigned_responder_id == responder.id, SOSAlert.status.in_([SOS_ASSIGNED, SOS_RESPONDING]))
        .order_by(SOSAlert.created_at.desc())
        .first()
    )
    if sos:
        _maybe_escalate(db, sos)
        db.refresh(sos)
        # Escalation may have just reassigned this SOS away from the caller.
        if sos.assigned_responder_id != responder.id:
            return None
    return sos


@router.patch("/sos/{sos_id}/cancel", response_model=SOSOut)
def cancel_sos(sos_id: int, device_id: str, db: Session = Depends(get_db)):
    """Lets the reporting pilgrim call off their own false alarm - distinct
    from /resolve, which a responder/manager uses once help was rendered."""
    sos = db.query(SOSAlert).filter(SOSAlert.id == sos_id, SOSAlert.device_id == device_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")
    sos.status = SOS_RESOLVED
    sos.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sos)
    return sos


@router.get("/sos/{sos_id}", response_model=SOSStatusOut)
async def get_sos_status(sos_id: int, device_id: str, db: Session = Depends(get_db)):
    """Polled by the reporting pilgrim's own device - scoped by device_id
    (their locally-generated anonymous identity) rather than a login, the
    same pattern used for family/health-card lookups elsewhere."""
    sos = db.query(SOSAlert).filter(SOSAlert.id == sos_id, SOSAlert.device_id == device_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")
    _maybe_escalate(db, sos)

    responder_name = None
    distance_km = None
    duration_min = None
    if sos.assigned_responder_id:
        responder = db.query(User).filter(User.id == sos.assigned_responder_id).first()
        if responder:
            responder_name = responder.name
            if responder.current_lat is not None and responder.current_lng is not None:
                try:
                    route = await get_driving_route(responder.current_lat, responder.current_lng, sos.lat, sos.lng)
                    distance_km = route["distance_km"]
                    duration_min = route["duration_min"]
                except RouteUnavailable:
                    distance_km = haversine_km(responder.current_lat, responder.current_lng, sos.lat, sos.lng)

    return SOSStatusOut(
        id=sos.id,
        status=sos.status,
        responder_name=responder_name,
        distance_km=distance_km,
        duration_min=duration_min,
        created_at=sos.created_at,
    )


@router.get("/sos/{sos_id}/route")
async def get_sos_route(
    sos_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_SOS)),
):
    sos = db.query(SOSAlert).filter(SOSAlert.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")
    if not sos.assigned_responder_id:
        raise HTTPException(status_code=400, detail="No responder assigned yet")
    responder = db.query(User).filter(User.id == sos.assigned_responder_id).first()
    if not responder or responder.current_lat is None or responder.current_lng is None:
        raise HTTPException(status_code=400, detail="Responder's live location isn't available yet")
    try:
        return await get_driving_route(responder.current_lat, responder.current_lng, sos.lat, sos.lng)
    except RouteUnavailable as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.patch("/sos/{sos_id}/acknowledge", response_model=SOSOut)
def acknowledge_sos(
    sos_id: int,
    db: Session = Depends(get_db),
    responder: User = Depends(require_roles(ROLE_FIELD_TEAM, ROLE_VOLUNTEER)),
):
    sos = db.query(SOSAlert).filter(SOSAlert.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")
    if sos.assigned_responder_id != responder.id:
        raise HTTPException(status_code=403, detail="This SOS isn't assigned to you")
    if sos.status != SOS_ASSIGNED:
        raise HTTPException(status_code=400, detail="This SOS is no longer waiting on your acknowledgment")
    sos.status = SOS_RESPONDING
    sos.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sos)
    return sos


@router.patch("/sos/{sos_id}/reassign", response_model=SOSOut)
def reassign_sos(
    sos_id: int,
    payload: SOSReassign,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_SOS)),
):
    sos = db.query(SOSAlert).filter(SOSAlert.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")
    responder = db.query(User).filter(User.id == payload.responder_id).first()
    if not responder:
        raise HTTPException(status_code=404, detail="Responder not found")
    _assign(db, sos, responder)
    db.refresh(sos)
    return sos


@router.patch("/sos/{sos_id}/resolve", response_model=SOSOut)
def resolve_sos(
    sos_id: int,
    db: Session = Depends(get_db),
    responder: User = Depends(require_roles(ROLE_ADMIN, ROLE_VOLUNTEER_MANAGER, ROLE_FIELD_TEAM, ROLE_VOLUNTEER)),
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
