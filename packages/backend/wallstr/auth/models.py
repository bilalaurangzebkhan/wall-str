from datetime import datetime, timedelta
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils.types import PasswordType

from wallstr.auth.schemas import UserSettings
from wallstr.conf import settings
from wallstr.models.base import PydanticJSON, RecordModel, string_column, utc_now


class UserModel(RecordModel):
    __tablename__ = "auth_users"

    email: Mapped[EmailStr] = mapped_column(unique=True, index=True, nullable=False)
    username: Mapped[str] = string_column(32)
    fullname: Mapped[str] = string_column(128)
    password: Mapped[str | None] = mapped_column(
        PasswordType(
            schemes=["pbkdf2_sha512"],
            pdbkdf2_sha512__salt_size=16,
            pdbkdf2_sha512__rounds=25000,
        ),
        nullable=True,
    )

    settings: Mapped[UserSettings] = mapped_column(
        PydanticJSON(UserSettings), default=dict, server_default="{}"
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    sessions: Mapped[list["SessionModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SessionModel(RecordModel):
    __tablename__ = "auth_sessions"

    refresh_token: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user: Mapped[UserModel] = relationship(back_populates="sessions")

    user_agent: Mapped[str | None] = string_column(255)
    ip_addr: Mapped[str | None] = string_column(64)

    @property
    def is_expiring_soon(self) -> bool:
        return self.expires_at - utc_now() < timedelta(
            days=settings.JWT.refresh_token_expire_days // 3
        )
