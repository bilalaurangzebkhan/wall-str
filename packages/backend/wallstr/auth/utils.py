from datetime import timedelta
from uuid import UUID

from authlib.jose import jwt

from wallstr.conf import settings
from wallstr.models.base import utc_now


def generate_jwt(
    user_id: UUID,
    expires_in: timedelta = timedelta(minutes=settings.JWT.access_token_expire_minutes),
) -> str:
    header = {"alg": settings.JWT.algorithm, "typ": "JWT"}
    payload = {
        "iss": settings.JWT.issuer,
        "sub": str(user_id),
        "exp": utc_now() + expires_in,
        "iat": utc_now(),
    }
    b = jwt.encode(header, payload, settings.SECRET_KEY.get_secret_value())
    if not isinstance(b, bytes):
        raise ValueError("jwt.encode() must return bytes")
    return b.decode("utf-8")
