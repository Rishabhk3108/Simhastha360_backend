from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.task import (
    MIN_COMPLETION_PHOTOS,
    TASK_ACKNOWLEDGED,
    TASK_COMPLETE,
    TASK_REVIEW,
    TASK_UNASSIGNED,
    Task,
)
from app.models.user import (
    ROLE_ADMIN,
    ROLE_FIELD_TEAM,
    ROLE_VOLUNTEER,
    ROLE_VOLUNTEER_MANAGER,
    STATUS_APPROVED,
    User,
    VolunteerProfile,
)
from app.schemas.task import (
    PointsSummary,
    TaskAssign,
    TaskCreate,
    TaskOut,
    TaskPhotosSubmit,
    TaskReviewAction,
    TaskSuggestion,
)
from app.services.geo import haversine_km
from app.services.notifications import notify

router = APIRouter(prefix="/tasks", tags=["tasks"])

# "Admin" here follows the same split the rest of the app uses: the police/
# municipal volunteer managers run day-to-day task assignment and review,
# with the main admin role kept as an override, not removed from the loop.
MANAGES_TASKS = (ROLE_ADMIN, ROLE_VOLUNTEER_MANAGER)


@router.post("", response_model=TaskOut)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_TASKS)),
):
    task = Task(**payload.model_dump(), status=TASK_UNASSIGNED, created_by=manager.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str | None = None,
    zone_id: int | None = None,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_TASKS)),
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


@router.get("/mine/points", response_model=PointsSummary)
def my_points(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(ROLE_VOLUNTEER, ROLE_FIELD_TEAM)),
):
    completed = (
        db.query(Task)
        .filter(Task.assignee_id == user.id, Task.status == TASK_COMPLETE, Task.completed_at.isnot(None))
        .all()
    )
    today = date.today()
    total = sum(t.points for t in completed)
    today_total = sum(t.points for t in completed if t.completed_at.date() == today)
    return PointsSummary(today=today_total, total=total)


@router.get("/{task_id}/suggestions", response_model=list[TaskSuggestion])
def suggest_assignees(
    task_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_TASKS)),
):
    """Ranks approved, on-duty volunteers by skill/zone/distance fit. A simple,
    explainable scoring model - not a black box - since the manager makes the final call."""
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
        if task.lat is not None and task.lng is not None and profile.user.current_lat is not None and profile.user.current_lng is not None:
            distance_km = haversine_km(task.lat, task.lng, profile.user.current_lat, profile.user.current_lng)
            if distance_km < 5:
                score += max(0.0, 2.0 - distance_km / 2.5)
                reasons.append(f"~{distance_km:.1f} km from task location")
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
    manager: User = Depends(require_roles(*MANAGES_TASKS)),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    assignee = db.query(User).filter(User.id == payload.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")

    task.assignee_id = payload.assignee_id
    db.commit()
    db.refresh(task)

    notify(
        db,
        assignee,
        "New task assigned",
        f"{task.description} ({task.points} pts)",
        {"type": "task_assigned", "task_id": task.id},
    )
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


@router.patch("/{task_id}/submit-photos", response_model=TaskOut)
def submit_completion_photos(
    task_id: int,
    payload: TaskPhotosSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(ROLE_VOLUNTEER, ROLE_FIELD_TEAM)),
):
    if len(payload.photo_doc_ids) < MIN_COMPLETION_PHOTOS:
        raise HTTPException(status_code=400, detail=f"At least {MIN_COMPLETION_PHOTOS} photos are required")
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or task.assignee_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completion_photo_doc_ids = payload.photo_doc_ids
    task.status = TASK_REVIEW
    task.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/review", response_model=TaskOut)
def review_task(
    task_id: int,
    payload: TaskReviewAction,
    db: Session = Depends(get_db),
    manager: User = Depends(require_roles(*MANAGES_TASKS)),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.assignee_id:
        raise HTTPException(status_code=400, detail="Task has no assignee")
    assignee = db.query(User).filter(User.id == task.assignee_id).first()

    if payload.action == "approve":
        task.status = TASK_COMPLETE
        task.completed_at = datetime.now(timezone.utc)
        task.review_note = payload.note
        db.commit()
        db.refresh(task)
        notify(
            db,
            assignee,
            "Task approved",
            f"{task.points} points credited for: {task.description}",
            {"type": "task_approved", "task_id": task.id, "points": task.points},
        )
    elif payload.action == "reject":
        task.status = TASK_ACKNOWLEDGED
        task.review_note = payload.note
        db.commit()
        db.refresh(task)
        notify(
            db,
            assignee,
            "Task needs another look",
            payload.note or "Please resubmit completion photos.",
            {"type": "task_rejected", "task_id": task.id},
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

    return task
