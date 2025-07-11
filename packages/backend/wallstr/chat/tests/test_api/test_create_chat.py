import pytest
from fastapi.testclient import TestClient

from wallstr.auth.models import UserModel
from wallstr.auth.utils import generate_jwt
from wallstr.chat.schemas import Chat
from wallstr.documents.models import DocumentType


@pytest.mark.asyncio
async def test_create_chat_success(client: TestClient, alice: UserModel) -> None:
    token = generate_jwt(alice.id)
    response = client.post(
        "/chats",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Hello, this is a test message!",
            "documents": [{"filename": "test.pdf", "doc_type": DocumentType.PDF}],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, dict)
    chat = Chat.model_validate(data)
    assert chat.messages.items[0].content == "Hello, this is a test message!"
    assert chat.messages.items[0].role == "user"
    assert chat.messages.cursor is None
    pending_documents = chat.messages.items[0].pending_documents
    assert len(pending_documents) == 1
