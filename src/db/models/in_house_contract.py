import uuid
from datetime import date
from typing import Optional, Literal
from sqlalchemy import ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

from .base import Base

LanguageType = Literal["EN", "ZH", "EN-ZH"]

class InHouseContract(Base):
    __tablename__ = "InHouseContracts"

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
    version_group_id: Mapped[uuid.UUID] = mapped_column(
        "VersionGroupId",
        ForeignKey("InHouseContractVersionGroups.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("name", nullable=False)
    file_type: Mapped[str] = mapped_column("fileType", nullable=False)
    language: Mapped[Optional[LanguageType]] = mapped_column(
        Enum(
            "EN", "ZH", "EN-ZH"
        )
    )
    type: Mapped[str] = mapped_column("type")
    parties= mapped_column("parties", type_=JSONB(none_as_null=True))
    amounts= mapped_column("amounts", type_=JSONB(none_as_null=True))
    content= mapped_column("content", type_=JSONB(none_as_null=True))
    summary: Mapped[str] = mapped_column("summary")
    contentembedding = mapped_column(
        "contentEmbedding", Vector(1024), nullable=True
    )
    summaryembedding = mapped_column(
        "summaryEmbedding", Vector(1024), nullable=True
    )
    deleted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[date] = mapped_column("createdAt", nullable=False)
    updated_at: Mapped[Optional[date]] = mapped_column("updatedAt", nullable=False)
