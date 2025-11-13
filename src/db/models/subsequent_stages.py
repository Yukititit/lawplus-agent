import uuid
from datetime import date
from typing import Literal, Optional,List,Dict
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base





class SubsequentStage(Base):
    __tablename__ = "SubsequentStages"
    
    stage_id: Mapped[uuid.UUID]  = mapped_column("StageId", ForeignKey("Stages.id"))
    subsequent_stage_id: Mapped[uuid.UUID]  = mapped_column("SubsequentStageId", primary_key=True)
    duration: Mapped[Optional[int]] = mapped_column("duration")
    stage: Mapped["Stage"] = relationship("Stage", back_populates="subsequent_stages")

    # id: Mapped[uuid.UUID] = mapped_column(
    #     "id",
    #     primary_key=True,
    #     default=uuid.uuid4,
    #     server_default=text("uuid_generate_v4()"),
    # )
    # name: Mapped[str] = mapped_column("name")
    # time: Mapped[Optional[int]] = mapped_column("time")
    # stages: Mapped["Stages"] = relationship(back_populates="subsequent_stage")
    # stages_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("Stages.id"))