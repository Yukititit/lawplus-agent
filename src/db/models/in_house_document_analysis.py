import uuid
from datetime import date
from typing import Optional, Literal
from sqlalchemy import ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

InhseDocType = Literal[
    "Party Information",
    "Correspondence",
    "Pleadings",
    "Supporting Documents",
]

class InHouseDocumentAnalysis(Base):
    __tablename__ = "InHouseDocumentAnalysis"

    in_house_document_id: Mapped[uuid.UUID] = mapped_column(
        "InHouseDocumentId",
        ForeignKey("InHouseDocuments.id"),
        nullable=False,
        primary_key=True,
    )
    doc_type: Mapped[Optional[InhseDocType]] = mapped_column(
        "docType",
        Enum(
            "Party Information",
            "Correspondence",
            "Pleadings",
            "Supporting Documents",
            "Contracts"
        ),
    )
    summary: Mapped[Optional[str]] = mapped_column("summary")

    in_house_document: Mapped["InHouseDocument"] = relationship(
        back_populates="document_analysis"
    )