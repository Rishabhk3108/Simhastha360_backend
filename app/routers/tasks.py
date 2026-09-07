from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.task import TASK_ACKNOWLEDGED, TASK_COMPLETE, TASK_UNASSIGNED, Task
from app.models.user import (
    ROLE_ADMIN,
    ROLE_FIELD_TEAM,
    ROLE_VOLUNTEER,
    STATUS_APPROVED,
    User,
    VolunteerProfile,
)
from app.schemas.task import TaskAssign, TaskCreate, TaskOut, TaskSuggestion

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    task = Task(**payload.model_dump(), status=TASK_UNASSIGNED, created_by=admin.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str | None = None,
    zone_id: int | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if zone_id is not None:
        query = query.filter(Task.zone_id == zone_id)
    return query.order_by(Task.created_at.desc()).all()


@router.get("/mine", response_model=list[TaskOut])
def my_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(ROLE_VOLUNTEER, ROLE_FIELD_TEAM)),
):
    return db.query(Task).filter(Task.assignee_id == user.id).order_by(Task.created_at.desc()).all()


@router.get("/{task_id}/suggestions", response_model=list[TaskSuggestion])
def suggest_assignees(
    task_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    """Ranks approved, on-duty volunteers by skill/zone/availability fit. A simple,
    explainable scoring model - not a black box - since admin makes the final call."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    profiles = (
        db.query(VolunteerProfile)
        .filter(VolunteerProfile.status == STATUS_APPROVED, VolunteerProfile.on_duty.is_(True))
        .all()
    )

    suggestions = []
    for profile in profiles:
        score = 0.0
        reasons = []
        if task.zone_id is not None and profile.preferred_zone_id == task.zone_id:
            score += 2.0
            reasons.append("Preferred zone matches task zone")
        skills = [s.strip().lower() for s in profile.skills.split(",") if s.strip()]
        task_desc_lower = task.description.lower()
        matched_skills = [s for s in skills if s in task_desc_lower]
        if matched_skills:
            score += 1.0 * len(matched_skills)
            reasons.append(f"Skills match task description: {', '.join(matched_skills)}")
        score += 0.5  # already on-duty and approved
        reasons.append("Currently on duty and approved")

        suggestions.append(
            TaskSuggestion(user_id=profile.user_id, name=profile.user.name, score=score, reasons=reasons)
        )

    suggestions.sort(key=lambda s: s.score, reverse=True)
    return suggestions[:10]


@router.patch("/{task_id}/assign", response_model=TaskOut)
def assign_task(
    task_id: int,
    payload: TaskAssign,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(ROLE_ADMIN)),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.assignee_id = payload.assignee_id
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/acknowledge", response_model=TaskOut)
def acknowledge_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(ROLE_VOLUNTEER, ROLE_FIELD_TEAM)),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or task.assignee_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TASK_ACKNOWLEDGED
    task.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(ROLE_VOLUNTEER, ROLE_FIELD_TEAM)),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or task.assignee_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TASK_COMPLETE
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task
