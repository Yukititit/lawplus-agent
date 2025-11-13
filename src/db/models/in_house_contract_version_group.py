import uuid
from datetime import date
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class InHouseContractVersionGroup(Base):
    __tablename__ = "InHouseContractVersionGroups"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        "UploadedBy",
        ForeignKey("Users.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("name", nullable=False)
    createdAt: Mapped[date] = mapped_column("createdAt", nullable=False)
    updatedAt: Mapped[date] = mapped_column("updatedAt", nullable=False)
