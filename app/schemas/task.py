from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    description: str
    zone_id: int | None = None
    lat: float | None = None
    lng: float | None = None
    points: int = 0
    priority: str = "medium"
    ack_deadline_minutes: int = 15
    assignee_id: int | None = None


class TaskAssign(BaseModel):
    assignee_id: int


class TaskPhotosSubmit(BaseModel):
    photo_doc_ids: list[str]


class TaskReviewAction(BaseModel):
    action: str  # approve | reject
    note: str | None = None
    rating: float | None = None  # optional volunteer rating, settable on approve


class TaskOut(BaseModel):
    id: int
    description: str
    zone_id: int | None
    lat: float | None
    lng: float | None
    points: int
    priority: str
    status: str
    assignee_id: int | None
    ack_deadline_minutes: int
    completion_photo_doc_ids: list[str]
    review_note: str | None
    created_at: datetime
    acknowledged_at: datetime | None
    submitted_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class TaskSuggestion(BaseModel):
    user_id: int
    name: str
    score: float
    reasons: list[str]


class PointsSummary(BaseModel):
    today: int
    total: int
