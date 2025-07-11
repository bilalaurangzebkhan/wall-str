from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from wallstr.auth.schemas import AccessToken
from wallstr.models.base import utc_now


class AuthSession(BaseModel):
    user_id: UUID
    access_token: AccessToken


class AnonymSession(BaseModel):
    user_id: None = None
    access_token: None = None


bearer_security = HTTPBearer(auto_error=False)


class Authenticator:
    def __init__(self, allow_anonym: bool = False, allow_expired: bool = False) -> None:
        self.allow_anonym = allow_anonym
        self.allow_expired = allow_expired

    def __call__(
        self,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Depends(bearer_security)
        ],
    ) -> AuthSession | AnonymSession:
        if not credentials:
            if self.allow_anonym:
                return AnonymSession()
            raise self._unauthorized_exception("Not authenticated")

        try:
            access_token = AccessToken(token=credentials.credentials)
            payload = access_token.decode()

            if payload["exp"] < utc_now().timestamp() and not self.allow_expired:
                raise self._unauthorized_exception("Token expired")

            user_id = str(payload["sub"])
            return AuthSession(user_id=UUID(user_id), access_token=access_token)
        except ValueError:
            if not self.allow_anonym:
                raise self._unauthorized_exception("Not authenticated") from None
        return AnonymSession()

    def _unauthorized_exception(self, detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


Auth = Annotated[
    AuthSession, Depends(Authenticator(allow_anonym=False, allow_expired=False))
]
AuthExp = Annotated[
    AuthSession,
    Depends(Authenticator(allow_anonym=False, allow_expired=True)),
]
AuthOrAnonym = Annotated[
    AuthSession | AnonymSession,
    Depends(Authenticator(allow_anonym=True, allow_expired=False)),
]
AuthExpOrAnonym = Annotated[
    AuthSession | AnonymSession,
    Depends(Authenticator(allow_anonym=True, allow_expired=True)),
]
