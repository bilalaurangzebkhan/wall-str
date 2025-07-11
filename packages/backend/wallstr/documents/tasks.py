from uuid import UUID

import structlog
from dramatiq.middleware import CurrentMessage
from structlog.contextvars import bind_contextvars

from wallstr.documents.services import DocumentService
from wallstr.worker import dramatiq
from wallstr.worker.time_limit import TimeLimitException, time_limit

logger = structlog.get_logger()


@dramatiq.actor(priority=10, queue_name="parse")  # type: ignore
async def process_document(document_id: str) -> None:
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    bind_contextvars(document_id=document_id, job_id=ctx.message_id)
    logger.info("Processing document")
    db_session = ctx.options.get("session")
    if not db_session:
        raise Exception("No session")

    redis = ctx.options.get("redis")
    if not redis:
        raise Exception("No redis")

    document_svc = DocumentService(db_session, redis)
    try:
        async with time_limit(minutes=10):
            await document_svc.parse_document(UUID(document_id))
    except TimeLimitException:
        await document_svc.mark_document_errored(
            UUID(document_id), {"message": "Time limit exceeded", "code": "time_limit"}
        )
        raise
