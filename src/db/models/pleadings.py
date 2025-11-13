import uuid
from datetime import date
from typing import Literal, Optional,List
from sqlalchemy import  text,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base



class Pleading(Base):
    __tablename__ = "Pleadings"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column("name")
    stage_id:Mapped[str] = mapped_column("StageId",ForeignKey("Stages.id"))
    
    # belong_to_stage_name: Mapped[str]Stage(Stages) = mapped_column("belong_to_stage")
    description: Mapped[str] = mapped_column("desc")
    executor: Mapped[str] = mapped_column("executor")
    # subsequent_pleadings: Mapped[List["SubsequentPleadings"]] = relationship(
    #     "SubsequentPleadings",
    #     back_populates="pleadings",
    # )
    
    stage = relationship("Stage", back_populates="pleadings")
    
    subsequent_pleadings : Mapped[List["SubsequentPleading"]] = relationship(
        "SubsequentPleading",

    )
    def __repr__(self):
        return f"Pleading(id={self.id!r}, name={self.name!r})"
