from textwrap import indent
from uuid import UUID

import structlog
from langchain_core.messages import HumanMessage
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import WeaviateProperties

from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import debug

logger = structlog.get_logger()


async def get_rag(
    document_ids: list[UUID],
    user_id: UUID,
    content: str,
    *,
    distance: float = 0.73,
    limit: int = 50,
) -> list[HumanMessage]:
    if not document_ids:
        return []
    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    try:
        # Check if user's tenant exists
        tenant_id = str(user_id)
        collection = wvc.collections.get("Documents")
        if not await collection.tenants.get_by_names([tenant_id]):
            logger.info(f"Tenant {tenant_id} not found")
            return []

        response = await collection.with_tenant(tenant_id).query.near_text(
            filters=Filter.by_property("document_id").contains_any(document_ids),
            query=content,
            distance=distance,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
        )
        debug(response.objects)
        logger.info(f"RAG matches: {len(response.objects)}")

        context = "\n".join([_get_rag_line(prompt) for prompt in response.objects])
        if not context:
            return []
        return [
            HumanMessage(f"# RAG Context\n{context}"),
        ]
    finally:
        await wvc.close()


async def get_pages(
    user_id: UUID,
    document_ids: list[UUID],
    pages: list[int],
    *,
    limit: int | None = None,
) -> list[str]:
    """
    Don't use it until parsing adds page for every record_id
    """
    wvc = get_weaviate_client(with_openai=True)
    try:
        await wvc.connect()
        tenant_id = str(user_id)
        collection = wvc.collections.get("Documents")
        if not await collection.tenants.get_by_names([tenant_id]):
            logger.info(f"Tenant {tenant_id} not found")
            return []

        response = await collection.with_tenant(tenant_id).query.fetch_objects(
            filters=(
                Filter.by_property("document_id").contains_any(document_ids)
                # TODO: in parsing.version=1 page is stored in metadata.page
                & Filter.by_property("page").contains_any(pages)
            ),
            limit=limit,
        )

        return [str(obj.properties["text"]) for obj in response.objects]
    finally:
        await wvc.close()


def _get_rag_line(chunk: Object[WeaviateProperties, None]) -> str:
    text = str(chunk.properties["text"])
    return f"""
    ## id: {chunk.uuid}
    {indent(text, " " * 4)}
    """
