from datetime import datetime

from pydantic import BaseModel


class SOSCreate(BaseModel):
    device_id: str
    lat: float
    lng: float


class SOSOut(BaseModel):
    id: int
    device_id: str
    lat: float
    lng: float
    status: str
    assigned_responder_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class LostPersonCreate(BaseModel):
    reporter_device_id: str
    subject_name: str
    subject_age: int | None = None
    subject_photo_url: str | None = None
    last_seen_lat: float | None = None
    last_seen_lng: float | None = None


class LostPersonOut(BaseModel):
    id: int
    subject_name: str
    subject_age: int | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
