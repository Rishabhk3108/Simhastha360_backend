from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class GuardianInfo(BaseModel):
    name: str
    phone: str
    aadhar_number: str
    email: str | None = None
    relation_to_pilgrim: str


class PilgrimInfo(BaseModel):
    name: str
    phone: str
    aadhar_number: str
    age: int
    photo_base64: str | None = None
    samagra_id: str | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    pincode: str
    country: str = "India"
    medical_history: str | None = None


class PilgrimRegistration(BaseModel):
    registered_via: Literal["self", "guardian"]
    device_id: str
    pilgrim: PilgrimInfo
    guardian: GuardianInfo


class PilgrimRegistrationOut(BaseModel):
    pilgrim_id: int
    guardian_id: int
    name: str
    registered_via: str
    created_at: datetime
