from datetime import datetime

from pydantic import BaseModel


class PilgrimInfo(BaseModel):
    name: str
    phone: str
    aadhar_number: str
    password: str
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
    device_id: str
    pilgrim: PilgrimInfo


class PilgrimRegistrationOut(BaseModel):
    pilgrim_id: int
    name: str
    created_at: datetime


class PilgrimSummary(BaseModel):
    pilgrim_id: int
    name: str


class PilgrimLogin(BaseModel):
    aadhar_number: str
    password: str


class PilgrimDetailOut(BaseModel):
    name: str
    phone: str
    aadhar_number: str
    age: int
    photo_base64: str | None
    samagra_id: str | None
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    pincode: str
    country: str
    medical_history: str | None


class GuardianOut(BaseModel):
    name: str
    phone: str
    aadhar_number: str
    email: str | None
    relation_to_pilgrim: str


class PilgrimLoginOut(BaseModel):
    pilgrim_id: int
    pilgrim: PilgrimDetailOut
    guardian: GuardianOut | None


class PilgrimLinkTokenOut(BaseModel):
    token: str
    expires_at: datetime


class PilgrimLocationUpdate(BaseModel):
    device_id: str
    lat: float
    lng: float
