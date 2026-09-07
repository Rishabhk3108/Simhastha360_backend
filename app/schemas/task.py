from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    description: str
    zone_id: int | None = None
    priority: str = "medium"
    ack_deadline_minutes: int = 15
    assignee_id: int | None = None


class TaskAssign(BaseModel):
    assignee_id: int


class TaskOut(BaseModel):
    id: int
    description: str
    zone_id: int | None
    priority: str
    status: str
    assignee_id: int | None
    ack_deadline_minutes: int
    created_at: datetime
    acknowledged_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class TaskSuggestion(BaseModel):
    user_id: int
    name: str
    score: float
    reasons: list[str]
