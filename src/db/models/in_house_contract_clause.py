import uuid
from datetime import date
from typing import Optional, Literal
from sqlalchemy import ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .base import Base

class InHouseContractClause(Base):
    __tablename__ = "InHouseContractClauses"

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
    title: Mapped[str] = mapped_column("title", nullable=False)
    content: Mapped[str] = mapped_column("content", nullable=False)
    index: Mapped[int] = mapped_column("index", nullable=False)
    contentembedding = mapped_column(
        "contentEmbedding", Vector(1024), nullable=True
    )
