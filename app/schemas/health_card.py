from pydantic import BaseModel


class HealthCardCreate(BaseModel):
    device_id: str
    name: str
    emergency_contact: str
    allergies: str | None = None
    conditions: str | None = None
    blood_group: str | None = None


class HealthCardOut(BaseModel):
    qr_token: str
    name: str


class HealthCardSummary(BaseModel):
    name: str
    emergency_contact: str
    allergies: str | None
    conditions: str | None
    blood_group: str | None
