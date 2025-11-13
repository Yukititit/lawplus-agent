import uuid
from typing import Optional
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Transcript(Base):
    __tablename__ = "Transcripts"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        "UploadId", ForeignKey("Uploads.id"), nullable=False
    )
    start: Mapped[float] = mapped_column("start", nullable=False)
    end: Mapped[float] = mapped_column("end", nullable=False)
    text: Mapped[str] = mapped_column("text", nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column("speaker")
