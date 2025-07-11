from datetime import timedelta
from typing import Any
from uuid import UUID

from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError, DecodeError
from pydantic import BaseModel, ConfigDict, EmailStr

from wallstr.conf import settings
from wallstr.conf.llm_models import SUPPORTED_LLM_MODELS_TYPES
from wallstr.models.base import utc_now


class HTTPUnauthorizedError(BaseModel):
    detail: str


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    username: str | None
    fullname: str | None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    fullname: str

    settings: "UserSettings"


class AccessToken(BaseModel):
    token: str
    token_type: str = "bearer"

    @classmethod
    def from_auth_header(cls, auth_header: str) -> "AccessToken":
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid token scheme")
        return cls(token=token, token_type=scheme)

    def decode(self) -> dict[Any, Any]:
        try:
            payload: dict[Any, Any] = jwt.decode(
                self.token,
                settings.SECRET_KEY.get_secret_value(),
            )
            exp = payload.get("exp")
            if not exp:
                raise ValueError("Missed 'exp' claim in token")

            return payload
        except (ValueError, BadSignatureError, DecodeError) as e:
            raise ValueError(f"Invalid token: {e}") from e

    @property
    def can_renew(self) -> bool:
        """
        Determines if the token can be used for renewal, even if it's expired.
        A token is considered renewable if it is within the allowed leeway period.

        Returns:
            bool: True if the token is within the leeway period, False otherwise.
        """
        token_renewal_leeway = timedelta(
            days=settings.JWT.access_token_renewal_leeway_days
        ).total_seconds()
        payload = self.decode()
        current_timestamp = utc_now().timestamp()
        return (int(payload["exp"]) + token_renewal_leeway) >= current_timestamp


class RefreshToken(BaseModel):
    token: str


class TokenPair(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken


class UserSettings(BaseModel):
    llm_model: SUPPORTED_LLM_MODELS_TYPES | None = None
    simple_mode: bool | None = None
