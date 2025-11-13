import uuid
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Case(Base):
    __tablename__ = "Cases"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    case_nature_id: Mapped[uuid.UUID] = mapped_column(
        "CaseNatureId",
        ForeignKey("CaseNatures.id"),
    )
    law_firm_id: Mapped[uuid.UUID] = mapped_column(
        "LawFirmId",
        ForeignKey("LawFirms.id"),
    )
    assisted: Mapped[bool] = mapped_column("assisted", nullable=False)

    law_firm: Mapped["LawFirm"] = relationship(back_populates="cases")
    case_nature: Mapped["CaseNature"] = relationship(back_populates="cases")
    documents: Mapped[list["Document"]] = relationship(back_populates="case")
