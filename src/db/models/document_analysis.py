import uuid
from datetime import date
from typing import Literal, Optional, List
from sqlalchemy import ForeignKey, Enum, ARRAY, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

DocType = Literal[
    "Personal Info",
    "Supporting Documents",
    "Pleadings",
    "Correspondence",
]


class DocumentAnalysis(Base):
    __tablename__ = "DocAnalysis"

    upload_id: Mapped[uuid.UUID] = mapped_column(
        "UploadId", ForeignKey("Uploads.id"), primary_key=True
    )
    doc_type: Mapped[Optional[DocType]] = mapped_column(
        "docType",
        Enum(
            "Personal Info", "Supporting Documents", "Pleadings", "Correspondence", ""
        ),
        nullable=True,
    )
    summary: Mapped[Optional[str]] = mapped_column("summary")
    dated: Mapped[Optional[date]] = mapped_column("dated")
    tags: Mapped[Optional[List[str]]] = mapped_column("tags", ARRAY(String))

    # upload: Mapped["Upload"] = relationship(back_populates="document_analysis")