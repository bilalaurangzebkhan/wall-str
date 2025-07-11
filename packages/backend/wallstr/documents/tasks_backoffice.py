import asyncio
import itertools
from uuid import UUID

import structlog
from dramatiq import group
from dramatiq.middleware import CurrentMessage
from weaviate.classes.query import Filter

from wallstr.documents.models import DocumentModel
from wallstr.documents.pdf_parser import PdfParser
from wallstr.documents.services import DocumentService
from wallstr.documents.tasks import process_document
from wallstr.worker import dramatiq

logger = structlog.get_logger()


@dramatiq.actor(priority=10, queue_name="parse", time_limit=3 * 60 * 60 * 1000)  # type: ignore
async def reprocess_documents(all_: bool = False) -> None:
    ctx = CurrentMessage.get_current_message()
    if not ctx:
        raise Exception("No ctx message")

    logger.info(f"Reprocess the documents all={all_}")

    if all_:
        raise Exception(f"Not implemented all={all_} reparsing")

    db_session = ctx.options["session"]
    redis = ctx.options["redis"]
    wvc = ctx.options["wvc"]

    await wvc.connect()
    document_svc = DocumentService(db_session, redis)

    collection_name = "Documents"
    collection = wvc.collections.get(collection_name)
    tenants = await collection.tenants.get()
    await wvc.close()

    total_documents = 0
    for tenant_id in tenants:
        document_ids = set()

        await wvc.connect()
        wvc_offset = 0
        wvc_limit = 100
        while True:
            data = await collection.with_tenant(tenant_id).query.fetch_objects(
                return_properties=["document_id"],
                filters=(
                    Filter.by_property("version").not_equal(PdfParser.version)
                    | Filter.by_property("inference_model").not_equal(
                        PdfParser.inference_model
                    )
                ),
                limit=wvc_limit,
                offset=wvc_offset,
            )
            wvc_offset += wvc_limit

            if not data.objects:
                break

            document_ids |= {obj.properties["document_id"] for obj in data.objects}
        await wvc.close()

        logger.info(f"Found {len(document_ids)} documents for tenant {tenant_id}")
        # TODO: there is limitation of dramatiq and pika in concurrency model
        # pika isn't threadsafe and it leads to the problem with asyncio parallel message group enqueuing
        limit = 1
        documents_per_tenant = 0
        for chunk in itertools.batched(document_ids, limit):
            documents = [
                document
                for document in [
                    await document_svc.get_document(document_id)
                    for document_id in chunk
                ]
                if document and document.can_parse
            ]

            def parse_documents(documents: list[DocumentModel]) -> None:
                g = group(  # type: ignore[no-untyped-call]
                    [
                        process_document.message_with_options(
                            kwargs={"document_id": str(document.id)}, priority=100
                        )
                        for document in documents
                    ]
                ).run()
                g.wait(timeout=10 * 60 * 1000)

            loop = asyncio.get_running_loop()
            try:
                if len(documents) != 1:
                    raise Exception(
                        f"Invalid documents count: {len(documents)}, only 1 document supported due to dramatiq and pika limitation"
                    )
                await loop.run_in_executor(None, parse_documents, documents)
            except Exception as e:
                logger.error(f"Failed to reprocess documents: {e}")
            else:
                total_documents += len(documents)
                documents_per_tenant += len(documents)
        logger.info(
            f"Filtered {documents_per_tenant}/{len(document_ids)} valid documents for tenant {tenant_id}"
        )
    logger.info(f"Reprocessing done, total documents: {total_documents}")
