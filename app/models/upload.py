from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(100))
    filename: Mapped[str] = mapped_column(String(255))
    data_base64: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
