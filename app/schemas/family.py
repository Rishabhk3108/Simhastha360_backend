from datetime import datetime

from pydantic import BaseModel


class FamilyGroupCreate(BaseModel):
    created_by_device_id: str
    member_name: str
    meeting_point_lat: float | None = None
    meeting_point_lng: float | None = None
    duration_hours: int = 24


class FamilyGroupJoin(BaseModel):
    device_id: str
    name: str


class FamilyLocationUpdate(BaseModel):
    device_id: str
    lat: float
    lng: float


class FamilyShareLinkCreate(BaseModel):
    device_id: str
    duration_hours: int = 24


class FamilyShareLinkOut(BaseModel):
    token: str
    expires_at: datetime


class PublicFamilyStatus(BaseModel):
    last_known_lat: float | None
    last_known_lng: float | None
    last_seen_at: datetime | None
    zone_name: str | None
    crowd_level: str | None
