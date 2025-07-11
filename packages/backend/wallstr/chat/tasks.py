from collections.abc import Sequence
from pathlib import Path
from textwrap import dedent
from typing import cast
from uuid import UUID, uuid4

import structlog
from dramatiq.middleware import CurrentMessage
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import bind_contextvars

from wallstr.auth.services import UserService
from wallstr.chat.memo.tasks import generate_memo
from wallstr.chat.models import (
    ChatMessageModel,
    ChatMessageRole,
    ChatMessageType,
    ChatModel,
)
from wallstr.chat.schemas import (
    ChatMessageEndSSE,
    ChatMessageSSE,
    ChatMessageStartSSE,
    ChatTitleUpdatedSSE,
)
from wallstr.chat.services import ChatService
from wallstr.conf.llm_models import SUPPORTED_LLM_MODELS_TYPES
from wallstr.core.llm import PROMPTS, get_llm, interleave_messages
from wallstr.core.rate_limiters import get_rate_limiter
from wallstr.documents.llm import get_rag
from wallstr.documents.models import DocumentStatus
from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import debug
from wallstr.worker import dramatiq

logger = structlog.get_logger()


@dramatiq.actor  # type: ignore
async def process_chat_message(
    message_id: str, model: SUPPORTED_LLM_MODELS_TYPES = "gpt-4o"
) -> None:
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    db_session = ctx.options.get("session")
    if not db_session:
        raise Exception("No session")

    chat_svc = ChatService(db_session)
    message = await chat_svc.get_chat_message(UUID(message_id))
    if not message:
        raise Exception("Message not found")

    if not message.content:
        # Not reply on an empty message
        return

    redis = ctx.options.get("redis")
    if not redis:
        raise Exception("No redis")

    bind_contextvars(chat_id=message.chat_id, message_id=message.id)

    user_svc = UserService(db_session)
    user = await user_svc.get_user(message.user_id)
    if not user:
        raise Exception("User not found")
    if user.deleted_at:
        raise Exception("User is deleted")

    bind_contextvars(user_id=user.id)
    # use @memo keyword to trigger building a memo
    is_memo = "@memo" in message.content

    if is_memo:
        new_message = await chat_svc.create_chat_message(
            chat_id=message.chat_id,
            message="",
            role=ChatMessageRole.ASSISTANT,
            message_type=ChatMessageType.MEMO,
        )
        logger.info(f"Generating memo for message {message.id}")
        generate_memo.send(str(new_message.id), message.content)
        return

    topic = f"{message.user_id}:{message.chat_id}:{message.id}"
    new_message_id = uuid4()
    await redis.publish(
        topic,
        ChatMessageStartSSE(
            id=new_message_id, chat_id=message.chat_id
        ).model_dump_json(),
    )

    document_ids = await chat_svc.get_chat_document_ids(
        message.chat_id, status=DocumentStatus.READY
    )
    logger.info(f"Found {len(document_ids)} documents for chat {message.chat_id}")

    llm = get_llm(model=user.settings.llm_model or model)

    messages = (
        await get_simple_llm_messages(document_ids, message)
        if user.settings.simple_mode
        else await get_llm_messages(db_session, document_ids, message)
    )
    debug(messages)
    if isinstance(llm, ChatDeepSeek) and llm.model_name == "deepseek-reasoner":
        """
        Deepseek R1 requires interleaved messages in the input
        https://github.com/deepseek-ai/DeepSeek-R1/issues/21
        """
        messages = interleave_messages(messages)

    chunks: list[str] = []
    with get_openai_callback() as cb:
        kwargs = (
            {"stream_usage": True}
            if isinstance(llm, (ChatOpenAI, AzureChatOpenAI))
            else {}
        )
        async for chunk in llm.astream(
            messages,
            config=None,
            stop=None,
            **kwargs,
        ):
            chunk_content = chunk if isinstance(chunk, str) else chunk.content

            if not chunk_content:
                continue
            if not isinstance(chunk_content, str):
                # TODO: don't output dict content when type handled
                logger.error(f"Chunk content is not a string {chunk_content}")
                continue
            # strip leading new line on the start of the message
            # TODO: use langchain BaseChunk merging
            chunks.append(chunk_content.lstrip()) if len(
                chunks
            ) == 0 else chunks.append(chunk_content)
            await redis.publish(
                topic,
                ChatMessageSSE(
                    id=new_message_id, chat_id=message.chat_id, content=chunk_content
                ).model_dump_json(),
            )
    if isinstance(llm, (ChatOpenAI, AzureChatOpenAI)):
        logger.info(
            f"OpenAI tokens used: {cb.total_tokens:_}, cost: {cb.total_cost:.3f}$"
        )
    new_message = await chat_svc.create_chat_message(
        chat_id=message.chat_id,
        message="".join(chunks),
        role=ChatMessageRole.ASSISTANT,
    )
    debug("".join(chunks))

    # set chat title
    chat = await chat_svc.get_chat(message.chat_id, message.user_id)
    if chat:
        title = await derive_chat_title(
            db_session,
            chat,
            allow_rewrite=True,
            content=new_message.content,
            model=model,
            user_prompt=message.content,
        )
        if title:
            await redis.publish(
                f"{message.user_id}:{message.chat_id}",
                ChatTitleUpdatedSSE(
                    id=new_message_id,
                    content=title,
                ).model_dump_json(),
            )

    await redis.publish(
        topic,
        ChatMessageEndSSE(
            id=new_message_id,
            new_id=new_message.id,
            chat_id=new_message.chat_id,
            created_at=new_message.created_at,
            content=new_message.content,
        ).model_dump_json(),
    )


async def derive_chat_title(
    db_session: AsyncSession,
    chat: ChatModel,
    *,
    allow_rewrite: bool,
    content: str,
    model: SUPPORTED_LLM_MODELS_TYPES,
    user_prompt: str,
) -> str | None:
    if chat.title and not allow_rewrite:
        return None
    llm = get_llm(model=model)
    rate_limiter = get_rate_limiter(model)

    messages = [
        SystemMessage(PROMPTS.system_prompt),
        HumanMessage(
            content="""
            You need derive a title for the chat based on context in format as 'Company | Topic'.
            Context contains user prompt and LLM response
            Company is a name of the company
            Topic should be not longer than 3 words"
            """
        ),
        HumanMessage(content=f"User prompt: {user_prompt}"),
        HumanMessage(content=f"AI response: {content}"),
    ]
    await rate_limiter.acquire(llm, messages)
    with get_openai_callback() as cb:
        response = await llm.ainvoke(messages)
    logger.info(
        f"OpenAI tokens used for getting title: {cb.total_tokens:_}, cost: {cb.total_cost:.3f}$"
    )

    title = response if isinstance(response, str) else response.content
    if not title:
        logger.error("Title not derived")
        return None

    if not isinstance(title, str):
        logger.error("Title is not a string")
        return None

    chat_svc = ChatService(db_session)
    async with db_session.begin():
        if not allow_rewrite:
            synced_chat = await chat_svc.get_chat(chat.id, chat.user_id)
            if not synced_chat:
                logger.error(f"Chat {chat.id} not found")
                return None

            if synced_chat.title:
                logger.warning(f"Chat {synced_chat.id} already has a title")
                return None

        await chat_svc.set_chat_title(chat.id, title)
    return title


async def get_simple_llm_messages(
    document_ids: list[UUID], message: ChatMessageModel
) -> list[SystemMessage | HumanMessage | AIMessage]:
    rag = await get_rag(document_ids, message.user_id, message.content)
    messages: list[SystemMessage | HumanMessage | AIMessage] = [
        SystemMessage(PROMPTS.system_simple_prompt),
        *rag,
        HumanMessage(content=message.content),
    ]
    return messages


async def get_llm_messages(
    db_session: AsyncSession, document_ids: list[UUID], message: ChatMessageModel
) -> list[SystemMessage | HumanMessage | AIMessage]:
    if not document_ids:
        prompt = dedent("""
        Tell the user that he didn't upload any documents yet, and suggest to do it"
        Remind that the more documents he uploads, the better the AI will reply on his questions.
        As well point that you can work only with the documents that were uploaded to the chat.
        """)

        chat_svc = ChatService(db_session)
        all_document_ids = await chat_svc.get_chat_document_ids(message.chat_id)
        if len(all_document_ids):
            prompt = dedent("""
            Please inform the user that their documents are still being analyzed by the service
            and that they should send their message later once the processing is complete.
            """)

        return [
            HumanMessage(content=message.content),
            HumanMessage(prompt),
        ]

    rag = await get_rag(document_ids, message.user_id, message.content)
    messages: list[SystemMessage | HumanMessage | AIMessage]
    if not rag:
        messages = [
            SystemMessage(PROMPTS.system_prompt),
            HumanMessage(content=message.content),
            HumanMessage(
                content="Tell the user that you don't have needful data to provide the answer."
            ),
        ]
    else:
        messages = [
            SystemMessage(PROMPTS.system_prompt),
            *await get_prompts_examples(message),
            *rag,
            HumanMessage(content=message.content),
        ]

    return messages


async def get_history(
    db_session: AsyncSession, message: ChatMessageModel, limit: int = 15
) -> list[AIMessage]:
    """
    Retrieves last messages from the chat to provide context to the LLM.
    """
    async with db_session.begin():
        result = await db_session.execute(
            sql.select(ChatMessageModel)
            .filter_by(chat_id=message.chat_id, deleted_at=None)
            .where(
                ChatMessageModel.created_at < message.created_at,
            )
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
    messages = result.scalars().all()
    return [AIMessage(content=message.content) for message in messages]


async def get_prompts_examples(message: ChatMessageModel) -> list[SystemMessage]:
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        collection = wvc.collections.get("Prompts")
        response = await collection.query.near_text(
            query=message.content,
            certainty=0.5,
            limit=10,
        )
        return [
            SystemMessage(f"""
        Example of response you provide:
        {"\n".join([f"- {prompt.properties["reply"]}" for prompt in response.objects])}
        """)
        ]
    finally:
        await wvc.close()
