from typing import Any, TypeVar

import logfire
from dramatiq import Broker, Message, Worker
from dramatiq.asyncio import get_event_loop_thread
from dramatiq.middleware import AsyncIO
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from weaviate import WeaviateAsyncClient

from wallstr.conf import settings
from wallstr.db import AsyncSessionMaker, create_async_engine, create_session_maker
from wallstr.documents.weaviate import get_weaviate_client

T = TypeVar("T")


class AsyncSessionMiddleware(AsyncIO):
    """Middleware that provides an async session for each actor and manages the AsyncIO event loop."""

    def __init__(self) -> None:
        super().__init__()  # type: ignore[no-untyped-call]
        self.engine: AsyncEngine
        self.session_maker: AsyncSessionMaker
        self.wvc: WeaviateAsyncClient

    def before_worker_boot(self, broker: Broker, worker: Worker) -> None:
        super().before_worker_boot(broker, worker)  # type: ignore[no-untyped-call]
        self.redis = Redis.from_url(settings.REDIS_URL.get_secret_value())
        self.engine = create_async_engine(settings.DATABASE_URL, "dramatiq-worker")
        self.session_maker = create_session_maker(self.engine)
        self.wvc = get_weaviate_client(with_openai=True)

        if settings.LOGFIRE_TOKEN:
            logfire.instrument_sqlalchemy(self.engine)

    def before_process_message(self, broker: Broker, message: Message[T]) -> None:
        super().before_process_message(broker, message)  # type: ignore[no-untyped-call]
        if not self.session_maker:
            raise RuntimeError("Session maker not initialized")
        message.options["session_maker"] = self.session_maker
        message.options["session"] = self.session_maker()
        message.options["redis"] = self.redis
        message.options["wvc"] = self.wvc

    def after_process_message(
        self,
        broker: Broker,
        message: Message[T],
        *,
        result: Any | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Called after a message is processed. Closes the session."""
        event_loop_thread = get_event_loop_thread()

        session: AsyncSession | None = message.options.get("session")
        if event_loop_thread and session:
            event_loop_thread.run_coroutine(session.close())

        super().after_process_message(
            broker, message, result=result, exception=exception
        )  # type: ignore[no-untyped-call]

    def before_worker_shutdown(self, broker: Broker, worker: Worker) -> None:
        event_loop_thread = get_event_loop_thread()

        if event_loop_thread and self.engine:
            event_loop_thread.run_coroutine(self.engine.dispose())

        if event_loop_thread and self.redis:
            event_loop_thread.run_coroutine(self.redis.aclose())

        super().before_worker_shutdown(broker, worker)  # type: ignore[no-untyped-call]
