from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from wallstr.auth.models import UserModel
from wallstr.auth.utils import generate_jwt
from wallstr.chat.models import ChatModel
from wallstr.documents.models import DocumentType


@pytest.mark.asyncio
async def test_send_chat_message_success(
    client: TestClient, alice: UserModel, chat: ChatModel
) -> None:
    token = generate_jwt(alice.id)
    response = client.post(
        f"/chats/{chat.slug}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Hello, this is a test message!",
            "documents": [{"filename": "test.pdf", "doc_type": DocumentType.PDF}],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello, this is a test message!"
    assert data["role"] == "user"
    assert len(data["documents"]) == 1
    assert data["documents"][0]["filename"] == "test.pdf"
    assert data["pending_documents"][0]["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_send_chat_message_empty_message_and_docs(
    client: TestClient, alice: UserModel, chat: ChatModel
) -> None:
    token = generate_jwt(alice.id)
    response = client.post(
        f"/chats/{chat.slug}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": None,
            "documents": [],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot send empty message"


@pytest.mark.asyncio
async def test_send_chat_message_with_only_document(
    client: TestClient, alice: UserModel, chat: ChatModel
) -> None:
    token = generate_jwt(alice.id)
    response = client.post(
        f"/chats/{chat.slug}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": None,
            "documents": [{"filename": "test.pdf", "doc_type": DocumentType.PDF}],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == ""
    assert len(data["documents"]) == 1
    assert data["documents"][0]["filename"] == "test.pdf"
    assert data["pending_documents"][0]["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_send_chat_message_chat_not_found(
    client: TestClient, alice: UserModel
) -> None:
    token = generate_jwt(alice.id)
    response = client.post(
        "/chats/non-existent-chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Hello!",
            "documents": [],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Chat not found"


@pytest.mark.asyncio
async def test_send_chat_message_unauthorized_chat(
    client: TestClient, chat: ChatModel
) -> None:
    token = generate_jwt(uuid4())
    response = client.post(
        f"/chats/{chat.slug}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Hello!",
            "documents": [],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Chat not found"
