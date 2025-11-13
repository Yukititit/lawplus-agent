import uuid
from datetime import date
from typing import Optional
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DocEvent(Base):
    __tablename__ = "DocEvents"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    doc_id: Mapped[uuid.UUID] = mapped_column(
        "DocId",
        ForeignKey("Docs.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("name")
    desc: Mapped[Optional[str]] = mapped_column("desc")
    source: Mapped[Optional[str]] = mapped_column("source")
    start: Mapped[date] = mapped_column("start")
    end: Mapped[Optional[date]] = mapped_column("end")

    doc: Mapped["Document"] = relationship(back_populates="events")