from datetime import datetime

from pydantic import BaseModel


class VolunteerApply(BaseModel):
    name: str
    phone: str
    password: str
    age: int | None = None
    city_state: str | None = None
    language: str = "en"
    skills: list[str] = []
    availability_dates: str | None = None
    preferred_zone_id: int | None = None
    id_proof_url: str | None = None


class VolunteerReviewAction(BaseModel):
    action: str  # approve | reject | request_info
    note: str | None = None


class VolunteerAvailabilityUpdate(BaseModel):
    on_duty: bool


class VolunteerOut(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str
    skills: str
    status: str
    on_duty: bool
    preferred_zone_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
