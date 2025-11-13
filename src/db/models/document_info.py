import uuid
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class DocumentInfo(Base):
    __tablename__ = "DocInfos"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        "UploadId", ForeignKey("Uploads.id"), primary_key=True
    )
    key: Mapped[str] = mapped_column("key", primary_key=True)
    group: Mapped[str] = mapped_column("group")
    content: Mapped[dict] = mapped_column("content", type_=JSONB(none_as_null=True))
    source: Mapped[str] = mapped_column("source")

    upload: Mapped["Upload"] = relationship(back_populates="document_infos")
