import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class LinkedAccount(Base):
    __tablename__ = "LinkedAccounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        "UserId",
        # ForeignKey("Users.id"),
        primary_key=True,
    )
    provider: Mapped[str] = mapped_column("provider")
    display_name: Mapped[str] = mapped_column("displayName")
    access_token: Mapped[str] = mapped_column("accessToken")
    refresh_token: Mapped[str] = mapped_column("refreshToken")
    expires_at: Mapped[int] = mapped_column("expiresAt")

    # user: Mapped["User"] = relationship(back_populates="linked_accounts")
