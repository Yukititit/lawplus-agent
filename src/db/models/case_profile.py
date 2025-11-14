import uuid
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CaseProfile(Base):
    __tablename__ = "CaseProfiles"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        "CaseProfileSessionId",
        ForeignKey("CaseProfileSessions.id"),
        nullable=False,
    )
    order: Mapped[int] = mapped_column("order")
    value: Mapped[str] = mapped_column("value")

    session: Mapped["CaseProfileSession"] = relationship(back_populates="profiles")
