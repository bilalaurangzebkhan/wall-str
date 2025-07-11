from uuid import uuid4

from authlib.jose import jwt

from wallstr.auth.utils import generate_jwt
from wallstr.conf import settings


def test_generate_jwt() -> None:
    user_id = uuid4()

    token = generate_jwt(user_id)
    assert token
    assert isinstance(token, str)

    payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value())
    assert payload["iss"] == settings.JWT.issuer
    assert payload["sub"] == str(user_id)
