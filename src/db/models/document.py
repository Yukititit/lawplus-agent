import uuid
from datetime import date
from typing import Optional, Literal, List
from sqlalchemy import ForeignKey, Enum, text, ARRAY, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

DocType = Literal[
    "Personal Info", "Supporting Documents", "Pleadings", "Correspondence", "Mediation"
]


class Document(Base):
    __tablename__ = "Docs"

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
    case_id: Mapped[uuid.UUID] = mapped_column(
        "CaseId",
        ForeignKey("Cases.id"),
        nullable=False,
    )
    type: Mapped[Optional[DocType]] = mapped_column(
        Enum(
            "Personal Info",
            "Supporting Documents",
            "Pleadings",
            "Correspondence",
            "Mediation",
        ),
        nullable=False,
    )
    name: Mapped[Optional[str]] = mapped_column("name")
    deleted: Mapped[Optional[bool]] = mapped_column("deleted", default=False)
    page: Mapped[Optional[int]] = mapped_column("page")
    split_suggestion: Mapped[Optional[List[List[int]]]] = mapped_column(
        "splitSuggestion", ARRAY(Integer, dimensions=2)
    )
    processed: Mapped[Optional[bool]] = mapped_column("processed", default=False)

    case: Mapped["Case"] = relationship(back_populates="documents")
    upload: Mapped["Upload"] = relationship(back_populates="document")

    updated_at: Mapped[Optional[date]] = mapped_column("updatedAt")
