import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import sql

from wallstr.auth.errors import (
    EmailAlreadyRegisteredError,
    EmailNotRegisteredError,
    InvalidPasswordError,
    PasswordNotSupportedError,
)
from wallstr.auth.models import SessionModel, UserModel
from wallstr.auth.schemas import SignUpRequest, UserSettings
from wallstr.auth.utils import generate_jwt
from wallstr.conf import settings
from wallstr.models.base import utc_now
from wallstr.services import BaseService


class AuthService(BaseService):
    async def signup_with_password(self, payload: SignUpRequest) -> UserModel:
        user_svc = UserService(self.db)
        async with self.tx():
            existing_user = await user_svc.get_user_by_email(payload.email)

            if existing_user:
                raise EmailAlreadyRegisteredError()

            return await user_svc.create_user(payload)

    async def signin_with_password(
        self, email: str, password: str, user_agent: str | None, ip_addr: str | None
    ) -> tuple[str, str]:
        user_svc = UserService(self.db)
        async with self.tx():
            user = await user_svc.get_user_by_email(email)
            if not user:
                raise EmailNotRegisteredError()

            if not user.password:
                raise PasswordNotSupportedError()

            if user.password != password:
                raise InvalidPasswordError()

            access_token = generate_jwt(user.id)
            session = await user_svc.create_session(user.id, user_agent, ip_addr)
        return access_token, session.refresh_token


class UserService(BaseService):
    async def get_user(self, id: UUID) -> UserModel | None:
        async with self.tx():
            result = await self.db.execute(sql.select(UserModel).filter_by(id=id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> UserModel | None:
        async with self.tx():
            result = await self.db.execute(sql.select(UserModel).filter_by(email=email))
        return result.scalar_one_or_none()

    async def create_user(self, payload: SignUpRequest) -> UserModel:
        async with self.tx():
            result = await self.db.execute(
                sql.insert(UserModel)
                .values(**payload.model_dump())
                .returning(UserModel)
            )
        return result.scalar_one()

    async def create_session(
        self, user_id: UUID, user_agent: str | None, ip_addr: str | None
    ) -> SessionModel:
        refresh_token = secrets.token_urlsafe(64)
        async with self.tx():
            result = await self.db.execute(
                sql.insert(SessionModel)
                .values(
                    refresh_token=refresh_token,
                    user_id=user_id,
                    user_agent=user_agent,
                    ip_addr=ip_addr,
                    expires_at=utc_now()
                    + timedelta(days=settings.JWT.refresh_token_expire_days),
                )
                .returning(SessionModel)
            )
        return result.scalar_one()

    async def get_session_by_token(self, refresh_token: str) -> SessionModel | None:
        async with self.tx():
            result = await self.db.execute(
                sql.select(SessionModel).where(
                    SessionModel.refresh_token == refresh_token,
                    SessionModel.expires_at > utc_now(),
                )
            )
        return result.scalar_one_or_none()

    async def renew_session(
        self, session: SessionModel, user_agent: str | None, ip_addr: str | None
    ) -> SessionModel:
        refresh_token = secrets.token_urlsafe(64)
        async with self.tx():
            result = await self.db.execute(
                sql.update(SessionModel)
                .filter_by(id=session.id)
                .values(
                    refresh_token=refresh_token,
                    user_agent=user_agent,
                    ip_addr=ip_addr,
                    expires_at=utc_now()
                    + timedelta(days=settings.JWT.refresh_token_expire_days),
                )
                .returning(SessionModel)
            )
        return result.scalar_one()

    async def revoke_session(self, refresh_token: str) -> None:
        async with self.tx():
            await self.db.execute(
                sql.delete(SessionModel).filter_by(refresh_token=refresh_token)
            )

    async def update_user_settings(
        self, user_id: UUID, settings: UserSettings
    ) -> UserModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(UserModel)
                .filter_by(id=user_id)
                .values(
                    settings=UserModel.settings.concat(
                        settings.model_dump(exclude_none=True)
                    )
                )
                .returning(UserModel)
            )
        return result.scalar_one()
