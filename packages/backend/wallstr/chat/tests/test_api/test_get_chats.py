import pytest
from fastapi.testclient import TestClient

from wallstr.auth.models import UserModel
from wallstr.auth.utils import generate_jwt


@pytest.mark.asyncio
async def test_get_chats_empty(client: TestClient, alice: UserModel) -> None:
    token = generate_jwt(alice.id)
    response = client.get("/chats", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["cursor"] is None


@pytest.mark.asyncio
async def test_get_chats_unauthorized(client: TestClient) -> None:
    response = client.get("/chats")
    assert response.status_code == 401
