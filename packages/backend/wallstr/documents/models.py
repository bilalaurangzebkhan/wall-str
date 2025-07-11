import enum
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from wallstr.models.base import RecordModel, string_column, utc_now


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"


class DocumentModel(RecordModel):
    __tablename__ = "documents"

    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            name="document_status",
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
    )
    error: Mapped[dict[str, str] | None] = mapped_column(
        JSONB(none_as_null=True),  # type: ignore[no-untyped-call]
        nullable=True,
    )
    errored_at: Mapped[datetime | None] = mapped_column(default=None)

    filename: Mapped[str] = string_column(length=255)
    file_size: Mapped[int] = mapped_column(nullable=True)
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(
            DocumentType,
            name="document_type",
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
    )
    storage_path: Mapped[str] = string_column(length=1024, nullable=False)

    @property
    def can_parse(self) -> bool:
        return not (
            self.status == DocumentStatus.PROCESSING
            and self.error is None
            and self.updated_at
            and utc_now() - self.updated_at <= timedelta(minutes=10)
        )
