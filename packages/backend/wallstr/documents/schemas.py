from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from wallstr.core.schemas import SSE
from wallstr.documents.models import DocumentStatus


class PendingDocument(BaseModel):
    id: UUID
    filename: str
    presigned_url: str


class Document(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    status: DocumentStatus

    error: str | None = None
    errored_at: datetime | None = None

    @field_validator("error", mode="before")
    def sanitize_error(cls, value: str | dict[str, str] | None) -> str | None:
        if not value:
            return None

        if isinstance(value, str):
            return value

        error_code = value.get("code")
        if not error_code:
            return "Unknown error"
        if error_code == "parse_error":
            return "Parsing error"
        return f"Error: {error_code}"


class DocumentStatusSSE(SSE):
    id: UUID
    status: DocumentStatus
    updated_at: datetime
    error: str | None
    errored_at: datetime | None

    @computed_field
    def type(self) -> str:
        return "document_status"


class DocumentSection(BaseModel):
    document_title: str
    document_url: str
    page_number: int
    bboxes: list[dict[str, Any]]


class DocumentPreview(BaseModel):
    document_title: str
    document_url: str
