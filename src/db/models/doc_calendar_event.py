import uuid
from datetime import date
from typing import Literal, Optional
from sqlalchemy import ForeignKey, text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


CalendarEvent = Literal[
    "Reponse Required",
    "Exact Date",
]


class DocCalendarEvent(Base):
    __tablename__ = "DocCalendarEvents"

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
    type: Mapped[Optional[CalendarEvent]] = mapped_column(
        "type",
        Enum(
            "Reponse Required",
            "Exact Date",
        ),
        nullable=True,
    )
    desc: Mapped[Optional[str]] = mapped_column("desc")
    source: Mapped[Optional[str]] = mapped_column("source")
    responseInDays: Mapped[Optional[int]] = mapped_column("responseInDays")
    dated: Mapped[Optional[date]] = mapped_column("dated")

    doc: Mapped["Document"] = relationship(back_populates="calendar_events")
