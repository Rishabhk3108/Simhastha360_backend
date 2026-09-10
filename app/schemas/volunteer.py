from datetime import datetime

from pydantic import BaseModel


class AvailabilitySlot(BaseModel):
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM


class VolunteerApply(BaseModel):
    name: str
    phone: str
    password: str
    age: int | None = None
    gender: str | None = None
    email: str | None = None
    language: str = "en"
    city_state: str | None = None
    permanent_address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    id_proof_type: str | None = None
    id_number: str | None = None
    id_proof_front_doc_id: str | None = None
    id_proof_back_doc_id: str | None = None
    photo_doc_id: str | None = None
    skills: list[str] = []
    languages: list[str] = []
    availability_slots: list[AvailabilitySlot] = []
    prior_experience: str | None = None
    tshirt_size: str | None = None
    organization_affiliation: str | None = None
    medical_conditions: str | None = None
    no_criminal_record: bool = False
    code_of_conduct_accepted: bool = False
    media_consent: bool = False
    preferred_zone_id: int | None = None


class VolunteerReviewAction(BaseModel):
    action: str  # approve | reject | request_info
    note: str | None = None
    rating: float | None = None  # settable on approve - the only rating source for now


class VolunteerAvailabilityUpdate(BaseModel):
    on_duty: bool


class VolunteerOut(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str
    age: int | None
    gender: str | None
    email: str | None
    city_state: str | None
    permanent_address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    id_proof_type: str | None
    id_number: str | None
    id_proof_front_doc_id: str | None
    id_proof_back_doc_id: str | None
    photo_doc_id: str | None
    skills: str
    languages: str
    availability_slots: list[AvailabilitySlot]
    prior_experience: str | None
    tshirt_size: str | None
    organization_affiliation: str | None
    medical_conditions: str | None
    no_criminal_record: bool
    code_of_conduct_accepted: bool
    media_consent: bool
    status: str
    review_note: str | None
    rating: float | None
    on_duty: bool
    preferred_zone_id: int | None
    current_lat: float | None
    current_lng: float | None
    location_updated_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
