from datetime import datetime

from pydantic import BaseModel


class CrowdReportCreate(BaseModel):
    zone_id: int
    type: str
    facility_id: int | None = None
    device_id: str
    lat: float | None = None
    lng: float | None = None


class CrowdReportOut(BaseModel):
    id: int
    zone_id: int
    type: str
    facility_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class IssueReportCreate(BaseModel):
    device_id: str
    description: str | None = None
    photo_doc_ids: list[str] = []
    lat: float | None = None
    lng: float | None = None


class IssueReportOut(BaseModel):
    id: int
    device_id: str
    description: str | None
    photo_doc_ids: list[str]
    lat: float | None
    lng: float | None
    status: str
    task_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class IssueReportCreateTask(BaseModel):
    priority: str = "medium"
    points: int = 10
    zone_id: int | None = None
    ack_deadline_minutes: int = 15
