import uuid
from datetime import date
from typing import Literal, Optional,List,Dict
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base




class Stage(Base):
    __tablename__ = "Stages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column("name")
    # relatedDocs: Mapped[Dict[str, int]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    # subsequent_stage: Mapped[list["SubsequentStages"]] =relationship("SubsequentStages", back_populates="stages") 
    case_nature_id: Mapped[uuid.UUID] = mapped_column('CaseNatureId', UUID(as_uuid=True), ForeignKey("CaseNatures.id"))
    
    case_nature: Mapped["CaseNature"] = relationship(back_populates="stages")

    related_docs: Mapped[Dict[str, int]] = mapped_column("relatedDocs", JSONB, server_default=text("'{}'::jsonb"))
    pleadings = relationship("Pleading", back_populates="stage")
    # related_docs: Mapped[Dict[str, int]] = mapped_column("relatedDocs", server_default=text("'{}'::jsonb"))
    subsequent_stages : Mapped[List["SubsequentStage"]] = relationship("SubsequentStage", back_populates="stage")
    
    
    def __repr__(self):
        return f"Stage(id={self.id!r}, name={self.name!r})"