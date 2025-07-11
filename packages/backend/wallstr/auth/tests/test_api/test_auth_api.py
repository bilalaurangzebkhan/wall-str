import secrets
from collections.abc import AsyncGenerator
from datetime import timedelta
from unittest.mock import ANY
from uuid import uuid4

import pytest
import pytest_mock
from fastapi.testclient import TestClient
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.auth.models import SessionModel, UserModel
from wallstr.auth.utils import generate_jwt
from wallstr.conf import settings
from wallstr.models.base import utc_now


@pytest.fixture
async def user_session(
    db_session: AsyncSession, alice: UserModel
) -> AsyncGenerator[SessionModel]:
    session = SessionModel()
    async with db_session.begin():
        result = await db_session.execute(
            sql.insert(SessionModel)
            .values(
                user_id=alice.id,
                refresh_token=secrets.token_urlsafe(64),
                user_agent="Test Device",
                ip_addr="127.0.0.1",
                expires_at=utc_now()
                + timedelta(days=settings.JWT.refresh_token_expire_days),
            )
            .returning(SessionModel)
        )
        await db_session.commit()
        session = result.scalar_one()
    yield session

    async with db_session.begin():
        await db_session.execute(sql.delete(SessionModel).filter_by(id=session.id))


async def test_signup_success(client: TestClient) -> None:
    response = client.post(
        "/auth/signup",
        json={
            "email": "alice.testcase@example.com",
            "password": "password123",
            "username": "alice.testcase",
            "fullname": "Alice Testcase",
        },
    )

    assert response.status_code == 201, response.json()
    data = response.json()
    assert data == {
        "id": ANY,
        "email": "alice.testcase@example.com",
        "username": "alice.testcase",
        "fullname": "Alice Testcase",
    }


async def test_signup_email_already_exists(
    alice: UserModel, client: TestClient
) -> None:
    response = client.post(
        "/auth/signup",
        json={
            "email": "alice@example.com",
            "password": "password123",
            "username": "bob.testcase",
            "fullname": "Bob Testcase",
        },
    )

    assert response.status_code == 409, response.json()
    assert response.json() == {"detail": "Email already registered"}


async def test_signin_success(client: TestClient, alice: UserModel) -> None:
    response = client.post(
        "/auth/signin", json={"email": "alice@example.com", "password": "password123"}
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert "token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    cookies = response.cookies
    assert "refresh_token" in cookies
    assert "HttpOnly" in response.headers["Set-Cookie"]


async def test_signin_invalid_credentials(client: TestClient, alice: UserModel) -> None:
    response = client.post(
        "/auth/signin",
        json={"email": "alice@example.com", "password": "wrong_password"},
    )

    assert response.status_code == 401, response.json()
    assert response.json() == {"detail": "Incorrect email or password"}
    assert "WWW-Authenticate" in response.headers


async def test_refresh_token(client: TestClient, user_session: SessionModel) -> None:
    token = generate_jwt(user_session.user_id)
    client.cookies["refresh_token"] = user_session.refresh_token
    response = client.post(
        "/auth/refresh-token", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert "token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


async def test_refresh_token_with_missed_access_token(
    client: TestClient, user_session: SessionModel
) -> None:
    client.cookies["refresh_token"] = user_session.refresh_token
    response = client.post("/auth/refresh-token")

    assert response.status_code == 401, response.json()
    assert response.json() == {"detail": "Not authenticated"}


async def test_refresh_token_with_expired_access_token(
    client: TestClient, user_session: SessionModel, mocker: pytest_mock.MockFixture
) -> None:
    token = generate_jwt(user_session.user_id)
    client.cookies["refresh_token"] = user_session.refresh_token

    future_datetime = utc_now() + timedelta(
        days=settings.JWT.access_token_renewal_leeway_days,
        minutes=settings.JWT.access_token_expire_minutes,
    )
    mock_utc_now = mocker.patch("wallstr.auth.schemas.utc_now")
    mock_utc_now.return_value = future_datetime
    response = client.post(
        "/auth/refresh-token", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401, response.json()
    assert response.json() == {"detail": "Invalid access token"}


async def test_refresh_token_invalid(
    client: TestClient, user_session: SessionModel
) -> None:
    token = generate_jwt(user_session.user_id)
    client.cookies["refresh_token"] = secrets.token_urlsafe(64)

    response = client.post(
        "/auth/refresh-token", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401, response.json()
    assert response.json() == {"detail": "Invalid or expired refresh token"}


async def test_refresh_token_with_new_session(
    client: TestClient, user_session: SessionModel, mocker: pytest_mock.MockFixture
) -> None:
    token = generate_jwt(user_session.user_id)
    client.cookies["refresh_token"] = user_session.refresh_token

    future_datetime = utc_now() + timedelta(
        days=settings.JWT.refresh_token_expire_days
        - settings.JWT.refresh_token_expire_days // 3
    )
    mock_utc_now = mocker.patch("wallstr.auth.models.utc_now")
    mock_utc_now.return_value = future_datetime
    response = client.post(
        "/auth/refresh-token", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert "token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert response.cookies["refresh_token"] != user_session.refresh_token


async def test_success_signout(client: TestClient, user_session: SessionModel) -> None:
    response = client.post(
        "/auth/signout",
        json={
            "token": user_session.refresh_token,
        },
    )

    assert response.status_code == 204


async def test_get_current_user_success(client: TestClient, alice: UserModel) -> None:
    token = generate_jwt(alice.id)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data == {
        "id": str(alice.id),
        "email": alice.email,
        "username": alice.username,
        "fullname": alice.fullname,
    }


async def test_get_current_user_no_auth(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401, response.json()


async def test_get_current_user_invalid_token(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401, response.json()


async def test_get_current_user_expired_token(
    client: TestClient, alice: UserModel
) -> None:
    token = generate_jwt(alice.id, expires_in=timedelta(minutes=-5))
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401, response.json()


async def test_get_current_user_not_found(client: TestClient) -> None:
    token = generate_jwt(uuid4())

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404, response.json()
    assert response.json() == {"detail": "User not found"}
