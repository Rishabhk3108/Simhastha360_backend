import httpx
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def notify(db: Session, user: User, title: str, body: str, data: dict | None = None) -> None:
    """Records a durable in-app notification and best-effort sends an Expo
    push. Push delivery failing (no token yet, network hiccup, revoked
    token) must never block the underlying action (task assignment,
    approval, etc.) - the in-app row is the source of truth either way."""
    db.add(Notification(user_id=user.id, title=title, body=body, data=data or {}))
    db.commit()

    if not user.expo_push_token:
        return
    try:
        httpx.post(
            EXPO_PUSH_URL,
            json={"to": user.expo_push_token, "title": title, "body": body, "data": data or {}},
            headers={"Content-Type": "application/json"},
            timeout=5.0,
        )
    except httpx.HTTPError:
        pass
