import uuid
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DocumentParty(Base):
    __tablename__ = "DocParties"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
    )
    upload_id: Mapped[uuid.UUID] = mapped_column("UploadId", ForeignKey("Uploads.id"))
    name: Mapped[str] = mapped_column("name")
    relation: Mapped[str] = mapped_column("relationship")

    upload: Mapped["Upload"] = relationship(back_populates="document_parties")
    document_party_infos: Mapped[list["DocumentPartyInfo"]] = relationship(
        back_populates="document_party"
    )
