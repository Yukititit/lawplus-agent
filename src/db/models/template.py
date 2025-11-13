import uuid
from datetime import date
from typing import Optional, Literal
from sqlalchemy import ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

StatusType = Literal["Processing", "Ready", "Failed"]


class Template(Base):
    __tablename__ = "Templates"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        "UploadId",
        ForeignKey("Uploads.id"),
        nullable=False,
        unique=True,
    )
    status: Mapped[Optional[StatusType]] = mapped_column(
        Enum("Processing", "Ready", "Failed"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("name")
    content: Mapped[Optional[str]] = mapped_column("content")
    deleted: Mapped[bool] = mapped_column(default=False)

    upload: Mapped["Upload"] = relationship(back_populates="template")