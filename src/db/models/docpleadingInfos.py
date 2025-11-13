import uuid
from datetime import date
from typing import Literal, Optional
from sqlalchemy import ForeignKey, text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base



class DocPleadingInfos(Base):
    __tablename__ = "DocPleadingInfos"


    
    doc_id: Mapped[uuid.UUID] = mapped_column(
        "DocId",
        ForeignKey("Docs.id"),
        nullable=False,
    )
    pleading_id: Mapped[uuid.UUID] = mapped_column("PleadingId",nullable=False,primary_key=True)

    
    
