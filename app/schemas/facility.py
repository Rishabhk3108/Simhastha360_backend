from datetime import datetime

from pydantic import BaseModel


class FacilityCreate(BaseModel):
    name: str
    type: str
    lat: float
    lng: float
    zone_id: int | None = None


class FacilityUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    lat: float | None = None
    lng: float | None = None
    zone_id: int | None = None
    status: str | None = None


class FacilityOut(BaseModel):
    id: int
    name: str
    type: str
    lat: float
    lng: float
    zone_id: int | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
