from datetime import datetime

from pydantic import BaseModel


class GuardianRegister(BaseModel):
    name: str
    phone: str
    password: str


class GuardianAccountOut(BaseModel):
    id: int
    name: str
    phone: str

    class Config:
        from_attributes = True


class LinkPilgrimRequest(BaseModel):
    token: str


class LinkedPilgrimOut(BaseModel):
    pilgrim_id: int
    name: str
    age: int | None
    photo_base64: str | None
    last_lat: float | None
    last_lng: float | None
    location_updated_at: datetime | None
    zone_name: str | None
    crowd_level: str | None
    has_active_sos: bool
