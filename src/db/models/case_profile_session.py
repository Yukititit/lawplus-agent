import uuid
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CaseProfileSession(Base):
    __tablename__ = "CaseProfileSessions"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    key: Mapped[str] = mapped_column("key")
    case_id: Mapped[uuid.UUID] = mapped_column(
        "CaseId",
        ForeignKey("Cases.id"),
        nullable=False,
    )

    case: Mapped["Case"] = relationship(back_populates="profile_sessions")
    profiles: Mapped[list["CaseProfile"]] = relationship(back_populates="session")
