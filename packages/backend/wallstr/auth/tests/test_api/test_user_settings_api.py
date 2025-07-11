from fastapi.testclient import TestClient

from wallstr.auth.models import UserModel
from wallstr.auth.utils import generate_jwt


async def test_set_llm_model(alice: UserModel, client: TestClient) -> None:
    token = generate_jwt(alice.id)
    response = client.post(
        "/auth/me/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "llm_model": "gpt-4o",
        },
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["settings"]["llm_model"] == "gpt-4o"


async def test_set_unsupported_llm_model(alice: UserModel, client: TestClient) -> None:
    token = generate_jwt(alice.id)
    response = client.post(
        "/auth/me/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "llm_model": "gpt-4o-unsupported",
        },
    )

    assert response.status_code == 422, response.json()


async def test_remove_llm_model(alice: UserModel, client: TestClient) -> None:
    token = generate_jwt(alice.id)
    client.post(
        "/auth/me/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "llm_model": None,
        },
    )
    response = client.post(
        "/auth/me/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "llm_model": None,
        },
    )

    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["settings"]["llm_model"] is None
