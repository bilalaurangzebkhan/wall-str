import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, TypedDict

import logfire
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from redis.asyncio import Redis
from structlog.contextvars import bind_contextvars, clear_contextvars
from weaviate import WeaviateAsyncClient

import wallstr.sentry  #  type: ignore[import]
from wallstr.auth.api import router as auth_router
from wallstr.auth.dependencies import Authenticator, bearer_security
from wallstr.chat.api import router as chat_router
from wallstr.conf import config, settings
from wallstr.core.schemas import AuthConfig, ConfigResponse
from wallstr.db import AsyncSessionMaker, create_async_engine, create_session_maker
from wallstr.documents.api import router as documents_router
from wallstr.documents.api_backoffice import router as documents_backoffice_router
from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import configure_logging
from wallstr.openapi import configure_openapi, generate_unique_id_function
from wallstr.sse.api import router as sse_router

logger = logging.getLogger(__name__)


class AppState(TypedDict):
    redis: Redis
    session_maker: AsyncSessionMaker
    wvc: WeaviateAsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[AppState, None]:
    engine = create_async_engine(settings.DATABASE_URL, "wallstr")
    session_maker = create_session_maker(engine)
    if settings.LOGFIRE_TOKEN:
        logfire.instrument_sqlalchemy(engine)

    redis = Redis.from_url(settings.REDIS_URL.get_secret_value())
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        yield {
            "redis": redis,
            "session_maker": session_maker,
            "wvc": wvc,
        }
    finally:
        try:
            await redis.aclose()
        except Exception as e:
            logger.exception(e)
        try:
            await engine.dispose()
        except Exception as e:
            logger.exception(e)
        try:
            await wvc.close()
        except Exception as e:
            logger.exception(e)


app = FastAPI(
    version=settings.VERSION,
    lifespan=lifespan,
    generate_unique_id_function=generate_unique_id_function(),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(documents_backoffice_router)
app.include_router(sse_router)


@app.middleware("http")
async def add_log_contextvars(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Adding additional parameters to the log context
    It's not possible to do with Dependency Injection

    https://github.com/encode/starlette/pull/1258#issuecomment-1236211856
    https://github.com/fastapi/fastapi/discussions/10124#discussioncomment-6788263
    https://github.com/fastapi/fastapi/discussions/8628
    """
    authenticator = Authenticator(allow_anonym=True, allow_expired=True)
    credentials = await bearer_security(request)
    auth_session = authenticator(credentials=credentials)
    if auth_session.user_id:
        bind_contextvars(user_id=auth_session.user_id)
    response = await call_next(request)
    clear_contextvars()
    return response


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"wallstr.chat v{settings.VERSION}"}


@app.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    return ConfigResponse(
        version=settings.VERSION,
        auth=AuthConfig(
            allow_signup=config.AUTH_ALLOW_SIGNUP,
            providers=config.AUTH_PROVIDERS,
        ),
        llm_models=config.LLM_MODELS,
    )


def set_log_attributes(
    request: Request | WebSocket, attrs: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(request, Request):
        return attrs
    authenticator = Authenticator(allow_anonym=True, allow_expired=True)

    # TODO: it's a copy of logic from fastapi.security.http.HTTPBearer.__call__
    # needs to raise an issue in FastAPI repo about async HTTPBearer.__call__
    # and refactor for using bearer_security directly
    authorization = request.headers.get("Authorization")
    scheme, _credentials = get_authorization_scheme_param(authorization)
    if not (authorization and scheme and _credentials):
        return attrs
    if scheme.lower() != "bearer":
        return attrs
    credentials = HTTPAuthorizationCredentials(scheme=scheme, credentials=_credentials)

    auth_session = authenticator(credentials=credentials)
    if auth_session.user_id:
        attrs["user_id"] = auth_session.user_id
    return attrs


configure_logging(name="api")
logfire.instrument_fastapi(
    app, capture_headers=False, request_attributes_mapper=set_log_attributes
)
configure_openapi(app)
