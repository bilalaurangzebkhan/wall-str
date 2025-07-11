import asyncio
from collections.abc import AsyncGenerator
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sse_starlette.sse import EventSourceResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from wallstr.auth.schemas import HTTPUnauthorizedError
from wallstr.auth.services import UserService
from wallstr.core.utils import uvicorn_should_exit
from wallstr.openapi import generate_unique_id_function

logger = structlog.get_logger()
router = APIRouter(
    prefix="/sse",
    generate_unique_id_function=generate_unique_id_function(4),
    responses={401: {"model": HTTPUnauthorizedError}},
)


@router.get("/")
async def connect(
    request: Request,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> EventSourceResponse:
    redis: Redis = request.state.redis

    # TODO: refresh_token is used for authentincation, needs to introduce additional cookie based auth
    # for sse only
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    auth_session = await user_svc.get_session_by_token(refresh_token)
    if not auth_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    clear_contextvars()
    bind_contextvars(user_id=auth_session.user_id)

    async def generator() -> AsyncGenerator[str, None]:
        async with redis.pubsub() as pubsub:
            await pubsub.psubscribe(f"{auth_session.user_id}:*")

            while not uvicorn_should_exit():
                if await request.is_disconnected():
                    await pubsub.aclose()
                    break

                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=5.0,
                    )

                    if message is not None:
                        yield message["data"].decode("utf-8")
                except asyncio.CancelledError as e:
                    await pubsub.aclose()
                    raise e
                except ConnectionError as e:
                    await pubsub.aclose()
                    raise e

    return EventSourceResponse(generator())
