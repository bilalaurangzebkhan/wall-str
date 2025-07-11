import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship

from wallstr.core.utils import generate_unique_slug
from wallstr.documents.models import DocumentModel
from wallstr.models.base import RecordModel, TimestampModel, string_column

if TYPE_CHECKING:
    from wallstr.chat.memo.models import MemoModel


class ChatModel(RecordModel):
    __tablename__ = "chats"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(
        String(12), unique=True, default=generate_unique_slug
    )
    title: Mapped[str] = string_column(length=255)
    messages: WriteOnlyMapped[list["ChatMessageModel"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )
    documents: Mapped[list[DocumentModel]] = relationship(
        secondary="chats_x_documents",
        lazy="selectin",
    )


class ChatMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessageType(str, enum.Enum):
    TEXT = "text"
    MEMO = "memo"


class ChatMessageModel(RecordModel):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index(
            "ix_chat_messages_chat_id_created_at",
            "chat_id",
            "created_at",
            postgresql_using="btree",
        ),
    )

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    role: Mapped[ChatMessageRole] = mapped_column(
        Enum(
            ChatMessageRole,
            name="chat_message_role",
            values_callable=lambda e: [i.value for i in e],
        ),
        nullable=False,
    )
    message_type: Mapped[ChatMessageType] = mapped_column(
        Enum(
            ChatMessageType,
            name="chat_message_type",
            values_callable=lambda e: [i.value for i in e],
        ),
        name="type",
        nullable=False,
        server_default=ChatMessageType.TEXT,
        default=ChatMessageType.TEXT,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    chat: Mapped[ChatModel] = relationship(back_populates="messages")
    documents: Mapped[list[DocumentModel]] = relationship(
        secondary="chat_messages_x_documents",
        lazy="selectin",
    )
    memo: Mapped["MemoModel"] = relationship(
        back_populates="chat_message", lazy="noload"
    )


class ChatMessageXDocumentModel(TimestampModel):
    __tablename__ = "chat_messages_x_documents"

    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), primary_key=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )


class ChatXDocumentModel(TimestampModel):
    __tablename__ = "chats_x_documents"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
