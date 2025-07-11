import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Text

from wallstr.chat.models import ChatMessageModel
from wallstr.models.base import RecordModel, string_column


class MemoType(str, enum.Enum):
    SHORT = "short"
    LONG = "long"


class MemoSectionModel(RecordModel):
    __tablename__ = "memo_sections"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    memo_id: Mapped[UUID] = mapped_column(
        ForeignKey("memos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    group: Mapped[str] = string_column(length=255, default=None)
    index: Mapped[int] = mapped_column(nullable=False)
    aspect: Mapped[str] = string_column(length=255, default=None)
    prompt: Mapped[str] = mapped_column(Text, default=None)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    memo: Mapped["MemoModel"] = relationship(back_populates="sections", lazy="raise")


class MemoModel(RecordModel):
    __tablename__ = "memos"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chat_message_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    memo_type: Mapped[MemoType] = mapped_column(
        Enum(
            MemoType,
            name="memo_type",
            values_callable=lambda e: [i.value for i in e],
        ),
        name="type",
        nullable=False,
    )

    chat_message: Mapped[ChatMessageModel] = relationship(
        back_populates="memo", lazy="raise"
    )

    sections: Mapped[list["MemoSectionModel"]] = relationship(
        back_populates="memo",
        lazy="raise",
        cascade="all, delete-orphan",
        order_by=(MemoSectionModel.group, MemoSectionModel.index),
    )
