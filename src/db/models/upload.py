import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Upload(Base):
    __tablename__ = "Uploads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    document: Mapped["Document"] = relationship(back_populates="upload")
    document_analysis: Mapped["DocumentAnalysis"] = relationship(
        back_populates="upload"
    )

    deleted: Mapped[bool] = mapped_column(default=False)
