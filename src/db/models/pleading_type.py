import uuid
from datetime import date
from typing import Optional
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PleadingType(Base):
    __tablename__ = "PleadingTypes"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column("name")

    doc: Mapped["Document"] = relationship(back_populates="events")