import secrets
from datetime import timedelta
from unittest import mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import SecretStr

from wallstr.auth.dependencies import (
    AnonymSession,
    Authenticator,
    AuthSession,
)
from wallstr.auth.utils import generate_jwt
from wallstr.conf import settings


@pytest.fixture
def auth() -> Authenticator:
    return Authenticator()


@pytest.fixture
def auth_anonym() -> Authenticator:
    return Authenticator(allow_anonym=True)


@pytest.fixture
def auth_expired() -> Authenticator:
    return Authenticator(allow_expired=True)


@pytest.fixture
def auth_anonym_expired() -> Authenticator:
    return Authenticator(allow_anonym=True, allow_expired=True)


def test_no_auth_header(auth: Authenticator) -> None:
    with pytest.raises(HTTPException) as exc:
        auth(None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Not authenticated"


def test_no_auth_header_anonym(auth_anonym: Authenticator) -> None:
    result = auth_anonym(None)
    assert isinstance(result, AnonymSession)
    assert result.user_id is None
    assert result.access_token is None


def test_invalid_token(auth: Authenticator) -> None:
    with mock.patch.object(
        settings, "SECRET_KEY", SecretStr(secrets.token_urlsafe(64))
    ):
        token = generate_jwt(uuid4())

    with pytest.raises(HTTPException) as exc:
        auth(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Not authenticated"


def test_invalid_token_anonym(auth_anonym: Authenticator) -> None:
    with mock.patch.object(
        settings, "SECRET_KEY", SecretStr(secrets.token_urlsafe(64))
    ):
        token = generate_jwt(uuid4())

    result = auth_anonym(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    )
    assert isinstance(result, AnonymSession)
    assert result.user_id is None
    assert result.access_token is None


def test_expired_token(auth: Authenticator) -> None:
    token = generate_jwt(uuid4(), expires_in=timedelta(minutes=-5))

    with pytest.raises(HTTPException) as exc:
        auth(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Token expired"


def test_expired_token_allow_expired(auth_expired: Authenticator) -> None:
    user_id = uuid4()
    token = generate_jwt(user_id, expires_in=timedelta(minutes=-5))

    result = auth_expired(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    )
    assert isinstance(result, AuthSession)
    assert result.user_id == user_id


def test_successful_authentication(auth: Authenticator) -> None:
    user_id = uuid4()
    token = generate_jwt(user_id)

    result = auth(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))
    assert isinstance(result, AuthSession)
    assert result.user_id == user_id
