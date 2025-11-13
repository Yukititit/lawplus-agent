import uuid
from typing import List, Optional, Literal
from sqlalchemy import ForeignKey, Enum, String
from sqlalchemy.types import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


ProfileType = Literal["Literal", "Keywords", "Number", "Text", "Boolean", "LiteralList"]


class ResearchProfile(Base):
    __tablename__ = "ResearchProfiles"

    key: Mapped[str] = mapped_column("key", primary_key=True)
    case_nature_id: Mapped[uuid.UUID] = mapped_column(
        "CaseNatureId", ForeignKey("CaseNatures.id"), primary_key=True
    )
    type: Mapped[ProfileType] = mapped_column(
        Enum("Literal", "Keywords", "Number", "Text", "Boolean", "LiteralList"),
        nullable=False,
    )
    weight: Mapped[int] = mapped_column("weight", nullable=False, default=1)
    extractable: Mapped[bool] = mapped_column("extractable", nullable=False)
    options: Mapped[Optional[List[str]]] = mapped_column("options", ARRAY(String))
    desc: Mapped[Optional[str]] = mapped_column("desc")

    case_nature: Mapped["CaseNature"] = relationship(back_populates="research_profiles")
