from pydantic import BaseModel


class PointOfInterestOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    icon: str
    lat: float
    lng: float

    class Config:
        from_attributes = True
