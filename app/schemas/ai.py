from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    lat: float | None = None
    lng: float | None = None


class ChatResponse(BaseModel):
    reply: str
    grounded_on: list[str]  # names of facilities/zones the answer cites


class FacilitySuggestion(BaseModel):
    cluster_center_lat: float
    cluster_center_lng: float
    report_count: int
    suggestion: str


class PredictiveAlert(BaseModel):
    zone_id: int
    zone_name: str
    current_level: str
    forecast_minutes: int
    forecast_level: str
    note: str
