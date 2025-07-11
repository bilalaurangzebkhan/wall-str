from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.auth.models import UserModel
from wallstr.chat.models import ChatMessageModel, ChatMessageRole, ChatModel


@pytest.fixture
async def chat(
    db_session: AsyncSession, alice: UserModel
) -> AsyncGenerator[ChatModel, None]:
    async with db_session.begin():
        result = await db_session.execute(
            sql.insert(ChatModel).values(user_id=alice.id).returning(ChatModel)
        )
        chat = result.scalar_one()

        await db_session.execute(
            sql.insert(ChatMessageModel).values(
                chat_id=chat.id,
                user_id=alice.id,
                role=ChatMessageRole.USER,
                content="Hello, how are you?",
            )
        )
    yield chat
    async with db_session.begin():
        await db_session.execute(
            sql.delete(ChatMessageModel).filter_by(chat_id=chat.id)
        )
        await db_session.execute(sql.delete(ChatModel).filter_by(id=chat.id))


@pytest.fixture
async def chat_with_messages(
    db_session: AsyncSession, alice: UserModel
) -> AsyncGenerator[ChatModel, None]:
    async with db_session.begin():
        result = await db_session.execute(
            sql.insert(ChatModel).values(user_id=alice.id).returning(ChatModel)
        )
        chat = result.scalar_one()

        messages = [
            {
                "chat_id": chat.id,
                "user_id": alice.id,
                "role": ChatMessageRole.USER,
                "content": f"User message {i}",
            }
            for i in range(5)
        ] + [
            {
                "chat_id": chat.id,
                "user_id": alice.id,
                "role": ChatMessageRole.ASSISTANT,
                "content": f"Assistant response {i}",
            }
            for i in range(5)
        ]

        await db_session.execute(sql.insert(ChatMessageModel).values(messages))

    yield chat
    async with db_session.begin():
        await db_session.execute(
            sql.delete(ChatMessageModel).filter_by(chat_id=chat.id)
        )
        await db_session.execute(sql.delete(ChatModel).filter_by(id=chat.id))
