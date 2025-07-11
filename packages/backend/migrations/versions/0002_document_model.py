"""document model

Revision ID: 0002
Revises: 0001
Create Date: 2025-02-18 23:32:29.897423

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum("pdf", "doc", "docx", "xls", "xlsx", name="document_type").create(
        op.get_bind()
    )  # type: ignore[no-untyped-call]
    sa.Enum(
        "uploading", "uploaded", "processing", "ready", name="document_status"
    ).create(op.get_bind())  # type: ignore[no-untyped-call]
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "uploading",
                "uploaded",
                "processing",
                "ready",
                name="document_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "error",
            postgresql.JSONB(astext_type=sa.Text(), none_as_null=True),  # type: ignore[no-untyped-call]
            nullable=True,
        ),
        sa.Column("errored_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column(
            "doc_type",
            postgresql.ENUM(
                "pdf",
                "doc",
                "docx",
                "xls",
                "xlsx",
                name="document_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index(
        op.f("ix_documents_user_id"), "documents", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_user_id"), table_name="documents")
    op.drop_table("documents")
    sa.Enum(
        "uploading", "uploaded", "processing", "ready", name="document_status"
    ).drop(op.get_bind())  # type: ignore[no-untyped-call]
    sa.Enum("pdf", "doc", "docx", "xls", "xlsx", name="document_type").drop(
        op.get_bind()
    )  # type: ignore[no-untyped-call]
