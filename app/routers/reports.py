from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.report import REPORT_CROWDED, CrowdReport
from app.models.user import ROLE_ADMIN, User
from app.models.zone import CROWD_GREEN, CROWD_RED, CROWD_YELLOW, Zone
from app.schemas.report import CrowdReportCreate, CrowdReportOut

router = APIRouter(prefix="/reports", tags=["reports"])

ESCALATION_WINDOW_MINUTES = 15
ESCALATION_DISTINCT_DEVICE_THRESHOLD = 5
CROWD_LEVEL_ORDER = [CROWD_GREEN, CROWD_YELLOW, CROWD_RED]


def _maybe_escalate_zone(db: Session, zone: Zone) -> None:
    """A single device spamming reports can't move a zone's status - escalation
    requires enough *distinct* devices reporting within the same short window."""
    since = datetime.now(timezone.utc) - timedelta(minutes=ESCALATION_WINDOW_MINUTES)
    recent = (
        db.query(CrowdReport)
        .filter(CrowdReport.zone_id == zone.id, CrowdReport.type == REPORT_CROWDED, CrowdReport.created_at >= since)
        .all()
    )
    distinct_devices = {r.device_id for r in recent}
    if len(distinct_devices) < ESCALATION_DISTINCT_DEVICE_THRESHOLD:
        return

    current_index = CROWD_LEVEL_ORDER.index(zone.crowd_level)
    if current_index < len(CROWD_LEVEL_ORDER) - 1:
        zone.crowd_level = CROWD_LEVEL_ORDER[current_index + 1]
        zone.updated_at = datetime.now(timezone.utc)
        db.commit()


@router.post("", response_model=CrowdReportOut)
def create_report(payload: CrowdReportCreate, db: Session = Depends(get_db)):
    report = CrowdReport(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)

    if report.type == REPORT_CROWDED:
        zone = db.query(Zone).filter(Zone.id == report.zone_id).first()
        if zone:
            _maybe_escalate_zone(db, zone)

    return report


@router.get("", response_model=list[CrowdReportOut])
def list_reports(
    zone_id: int | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    query = db.query(CrowdReport)
    if zone_id is not None:
        query = query.filter(CrowdReport.zone_id == zone_id)
    return query.order_by(CrowdReport.created_at.desc()).all()
