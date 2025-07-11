import asyncio
import base64
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import cache
from typing import cast
from uuid import uuid4

import structlog
from uvicorn import Server

logger = structlog.get_logger()


def generate_unique_slug(length: int = 12) -> str:
    random_uuid = uuid4()
    base64_slug = (
        base64.urlsafe_b64encode(random_uuid.bytes).decode("utf-8").rstrip("=")
    )
    return base64_slug[:length]


@cache
def uvicorn_server() -> Server:
    """
    Hack because sse-starlette cannot handle signals properly
    when using uvicorn.
    TODO: find better way to find server instance
    """
    for task in asyncio.all_tasks():
        coro = task.get_coro()
        if not coro:
            continue
        frame = coro.cr_frame  # type: ignore[attr-defined]
        if not frame:
            continue
        args = frame.f_locals
        self = args.get("self")
        if self and isinstance(self, Server):
            return cast(Server, self)
    raise RuntimeError("Uvicorn server not found")


def uvicorn_should_exit() -> bool:
    server = uvicorn_server()
    return server.should_exit


def debugger() -> None:
    try:
        from remote_pdb import RemotePdb  # type: ignore
    except ImportError:
        logger.warn("No remote_pdb, skipping debugger")
        return

    RemotePdb("127.0.0.1", 4444).set_trace()


@asynccontextmanager
async def tiktok(
    message: str, logger: structlog.BoundLogger = logger
) -> AsyncGenerator[None, None]:
    tik = time.perf_counter()
    logger.trace(message)
    try:
        yield
    except Exception:
        tok = time.perf_counter()
        elapsed = tok - tik
        elapsed_str = _format_elapsed_time(elapsed)
        logger.trace(f"{message} failed. {elapsed_str}")
        raise
    else:
        tok = time.perf_counter()
        elapsed = tok - tik
        elapsed_str = _format_elapsed_time(elapsed)
        logger.trace(f"{message} finished. {elapsed_str}")


def _format_elapsed_time(seconds: float) -> str:
    """Formats time in `xm ys` if > 60s, otherwise in seconds."""
    if seconds >= 60:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    return f"{seconds:.3f}s"
