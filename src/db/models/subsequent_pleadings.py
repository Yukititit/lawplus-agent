import uuid
from typing import Optional, List
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class SubsequentPleading(Base):
    __tablename__ = "SubsequentPleadings"

    pleading_id: Mapped[uuid.UUID]  = mapped_column("PleadingId", ForeignKey("Pleadings.id"))
    
    subsequent_pleading_id: Mapped[uuid.UUID]  = mapped_column("SubsequentPleadingId", primary_key=True)
    required_In_Days: Mapped[Optional[int]] = mapped_column("requiredInDays")

    # pleadings = relationship(
    #     "Pleading",
    #     back_populates="subsequent_pleadings",
    # )



    # ori_pleading = relationship(
    #     "Pleadings",
    # )
    # sub_pleadings = relationship(
    #     "Pleadings",
    #     back_populates="subsequent_pleadings",
    # )

    # Note: Removed subpleading_id as a primary key, as it seems unnecessary
    # If you need a composite primary key, clarify its purpose
    
    def __repr__(self):
        return f"SubsequentPleading(id={self.id!r}, name={self.name!r})"