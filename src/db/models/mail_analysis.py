import uuid
from typing import Optional, Literal
from sqlalchemy import ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base

Status = Literal["Pending", "Processing", "Waiting", "Success", "Failed", "Terminated"]


class MailAnalysis(Base):
    __tablename__ = "MailAnalysis"

    user_id: Mapped[uuid.UUID] = mapped_column(
        "UserId",
        # ForeignKey("Users.id"),
        primary_key=True,
    )
    mail_id: Mapped[str] = mapped_column(
        "mailId",
        primary_key=True,
    )
    status: Mapped[Status] = mapped_column(
        "status",
        nullable=False,
        default="Pending",
    )
    content: Mapped[dict] = mapped_column("content", type_=JSONB(none_as_null=True))
