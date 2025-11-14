import uuid
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CaseNature(Base):
    __tablename__ = "CaseNatures"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column("enName")

    cases: Mapped[list["Case"]] = relationship(back_populates="case_nature")