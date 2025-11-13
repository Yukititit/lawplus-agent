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


class InHouseDocument(Base):
    __tablename__ = "InHouseDocuments"

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
    type: Mapped[Optional[InhseDocType]] = mapped_column(
        Enum(
            "Party Information",
            "Correspondence",
            "Pleadings",
            "Supporting Documents",
        ),
        nullable=False,
    )
    name: Mapped[Optional[str]] = mapped_column("name")

    upload: Mapped["Upload"] = relationship(back_populates="inhse_document")
    document_analysis: Mapped["InHouseDocumentAnalysis"] = relationship(back_populates="in_house_document")