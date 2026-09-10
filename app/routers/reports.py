from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.report import (
    ISSUE_STATUS_DISMISSED,
    ISSUE_STATUS_NEW,
    ISSUE_STATUS_TASK_CREATED,
    REPORT_CROWDED,
    CrowdReport,
    IssueReport,
)
from app.models.task import TASK_UNASSIGNED, Task
from app.models.user import ROLE_ADMIN, ROLE_VOLUNTEER_MANAGER, User
from app.models.zone import CROWD_GREEN, CROWD_RED, CROWD_YELLOW, Zone
from app.schemas.report import (
    CrowdReportCreate,
    CrowdReportOut,
    IssueReportCreate,
    IssueReportCreateTask,
    IssueReportOut,
)
from app.schemas.task import TaskOut

router = APIRouter(prefix="/reports", tags=["reports"])

# Same split used across the volunteer/task features: the police/municipal
# volunteer managers triage incoming pilgrim reports day-to-day, with the
# main admin kept as an override.
MANAGES_REPORTS = (ROLE_ADMIN, ROLE_VOLUNTEER_MANAGER)

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


# Pilgrim-submitted issue reports - no auth required to file one (pilgrims
# aren't logged-in JWT users, they're identified by device_id like the rest
# of the pilgrim-facing features), but only volunteer managers/admin can see
# and triage the queue.
@router.post("/issues", response_model=IssueReportOut)
def create_issue_report(payload: IssueReportCreate, db: Session = Depends(get_db)):
    if len(payload.photo_doc_ids) < 1:
        raise HTTPException(status_code=400, detail="At least one photo is required")
    report = IssueReport(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/issues", response_model=list[IssueReportOut])
def list_issue_reports(
    status: str | None = None,
    task_id: int | None = None,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_REPORTS)),
):
    query = db.query(IssueReport)
    if status:
        query = query.filter(IssueReport.status == status)
    if task_id is not None:
        query = query.filter(IssueReport.task_id == task_id)
    return query.order_by(IssueReport.created_at.desc()).all()


@router.patch("/issues/{report_id}/dismiss", response_model=IssueReportOut)
def dismiss_issue_report(
    report_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_REPORTS)),
):
    report = db.query(IssueReport).filter(IssueReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ISSUE_STATUS_NEW:
        raise HTTPException(status_code=400, detail="Report has already been triaged")
    report.status = ISSUE_STATUS_DISMISSED
    db.commit()
    db.refresh(report)
    return report


@router.patch("/issues/{report_id}/create-task", response_model=TaskOut)
def create_task_from_issue_report(
    report_id: int,
    payload: IssueReportCreateTask,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_REPORTS)),
):
    report = db.query(IssueReport).filter(IssueReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ISSUE_STATUS_NEW:
        raise HTTPException(status_code=400, detail="Report has already been triaged")

    task = Task(
        description=report.description or "Pilgrim-reported issue (no description provided)",
        zone_id=payload.zone_id,
        lat=report.lat,
        lng=report.lng,
        points=payload.points,
        priority=payload.priority,
        ack_deadline_minutes=payload.ack_deadline_minutes,
        status=TASK_UNASSIGNED,
        created_by=manager.id,
    )
    db.add(task)
    db.flush()  # assigns task.id without committing yet
    report.status = ISSUE_STATUS_TASK_CREATED
    report.task_id = task.id
    db.commit()
    db.refresh(task)
    return task
