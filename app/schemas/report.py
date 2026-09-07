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
