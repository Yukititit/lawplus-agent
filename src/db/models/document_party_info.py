import uuid
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DocumentPartyInfo(Base):
    __tablename__ = "DocPartyInfos"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
    )
    doc_party_id: Mapped[uuid.UUID] = mapped_column(
        "DocPartyId", ForeignKey("DocParties.id")
    )
    key: Mapped[str] = mapped_column("key")
    content: Mapped[str] = mapped_column("content")
    source: Mapped[str] = mapped_column("source")

    document_party: Mapped["DocumentParty"] = relationship(
        back_populates="document_party_infos"
    )

    def __repr__(self):
        return f"DocumentPartyInfo(id={self.id}, doc_party_id={self.doc_party_id}, key={self.key}, content={self.content}, source={self.source})"