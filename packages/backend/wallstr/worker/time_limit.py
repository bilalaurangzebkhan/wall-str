import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager


class TimeLimitException(Exception): ...


@asynccontextmanager
async def time_limit(*, minutes: int = 0, seconds: int = 0) -> AsyncGenerator[None]:
    current_task = asyncio.current_task()
    total_seconds = (minutes * 60) + seconds

    async def watch() -> None:
        await asyncio.sleep(total_seconds)
        if current_task and not current_task.done():
            current_task.cancel()

    watcher = asyncio.create_task(watch())

    try:
        yield
    except asyncio.CancelledError:
        if not watcher.cancelled():
            raise TimeLimitException(
                f"Task exceeded time limit: {_format_elapsed_time(total_seconds)}"
            ) from None
        raise
    finally:
        watcher.cancel()


def _format_elapsed_time(seconds: float) -> str:
    """Formats time in `xm ys` if > 60s, otherwise in seconds."""
    if seconds >= 60:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    return f"{seconds}s"
