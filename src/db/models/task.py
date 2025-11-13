import uuid
from typing import Literal, Optional
from sqlalchemy import ForeignKey, Enum, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

TaskType = Literal[
    "Text Extraction",
    "Speech To Text",
    "Document Analysis",
    "Document Processing",
    "Image Understanding",
]
TaskStatus = Literal[
    "Pending", "Processing", "Waiting", "Success", "Failed", "Terminated"
]


class Task(Base):
    __tablename__ = "AITasks"

    id: Mapped[uuid.UUID] = mapped_column(
        "id",
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        "UploadId", ForeignKey("Uploads.id"), nullable=False
    )
    type: Mapped[TaskType] = mapped_column(
        Enum(
            "Text Extraction",
            "Speech To Text",
            "Document Analysis",
            "Document Processing",
            "Image Understanding",
        ),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum("Pending", "Processing", "Waiting", "Success", "Failed", "Terminated"),
        nullable=False,
        default="Pending",
    )
    computing_unit: Mapped[int] = mapped_column(
        "computingUnit", nullable=False, default=0
    )
    remark: Mapped[Optional[str]] = mapped_column("remark")
    az_operation: Mapped[Optional[str]] = mapped_column("azOperation")
