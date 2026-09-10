from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    title: str
    body: str
    data: dict
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PushTokenUpdate(BaseModel):
    expo_push_token: str
