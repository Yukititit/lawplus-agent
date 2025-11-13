import uuid
from datetime import date
from typing import Optional, Literal
from sqlalchemy import ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .base import Base

class InHouseContractEvent(Base):
    __tablename__ = "InHouseContractEvents"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        "ContractId",
        ForeignKey("InHouseContracts.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("name", nullable=False)
    desc: Mapped[str] = mapped_column("desc", nullable=False)
    start: Mapped[date] = mapped_column("start", nullable=False)
    end: Mapped[Optional[date]] = mapped_column("end")
    source: Mapped[Optional[str]] = mapped_column("source")
    type: Mapped[str] = mapped_column(
        "type"
    )