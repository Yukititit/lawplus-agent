import uuid
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TokenUsage(Base):
    __tablename__ = "TokenUsages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    feature_key: Mapped[str] = mapped_column("FeatureKey", nullable=False)
    law_firm_id: Mapped[uuid.UUID] = mapped_column(
        "LawFirmId", nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        "UserId", nullable=False
    )

    unit: Mapped[int] = mapped_column("unit", nullable=False)