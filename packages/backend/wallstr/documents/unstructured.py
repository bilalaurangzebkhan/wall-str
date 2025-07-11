import io
import tempfile
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

import boto3
import botocore.config
import structlog
from pydantic import Secret
from structlog.contextvars import bind_contextvars, clear_contextvars
from unstructured.chunking import dispatch
from unstructured.partition.pdf import partition_pdf
from unstructured_ingest.v2.interfaces import ProcessorConfig
from unstructured_ingest.v2.pipeline.pipeline import Pipeline
from unstructured_ingest.v2.processes.chunker import ChunkerConfig
from unstructured_ingest.v2.processes.connectors.fsspec.s3 import (
    S3AccessConfig,
    S3ConnectionConfig,
    S3DownloaderConfig,
    S3IndexerConfig,
)
from unstructured_ingest.v2.processes.connectors.weaviate.local import (
    LocalWeaviateAccessConfig,
    LocalWeaviateConnectionConfig,
    LocalWeaviateUploaderConfig,
    LocalWeaviateUploadStagerConfig,
)
from unstructured_ingest.v2.processes.embedder import EmbedderConfig
from unstructured_ingest.v2.processes.partitioner import PartitionerConfig
from weaviate.classes.query import Filter

from wallstr.conf import settings
from wallstr.documents.models import DocumentModel
from wallstr.documents.weaviate import get_weaviate_client

logger = structlog.get_logger()


async def upload_document_to_weaviate(remote_url: str, collection_name: str) -> None:
    """
    Unstructured ingest doesnt support uploading to self-hosted weaviate with custom endpoints.
    So this version works only with api=localhost:8080 grpc=localhost:50051

    https://github.com/Unstructured-IO/unstructured-ingest/issues/365

    Usage:
        remote_url = f"s3://{settings.STORAGE_BUCKET}/{document.storage_path}"
        await upload_document_to_weaviate(remote_url, collection_name="Documents")
    """
    wvc = get_weaviate_client()
    await wvc.connect()
    if not await wvc.collections.exists(collection_name):
        await wvc.close()
        raise Exception(
            f"Collection {collection_name} does not exist, run `task migrate_weaviate` first"
        )
    await wvc.close()

    with tempfile.TemporaryDirectory() as temp_dir:
        Pipeline.from_configs(
            context=ProcessorConfig(verbose=True),
            indexer_config=S3IndexerConfig(remote_url=remote_url),
            downloader_config=S3DownloaderConfig(
                download_dir=Path(temp_dir),
            ),
            source_connection_config=S3ConnectionConfig(
                access_config=Secret(
                    S3AccessConfig(
                        key=settings.STORAGE_ACCESS_KEY.get_secret_value(),
                        secret=settings.STORAGE_SECRET_KEY.get_secret_value(),
                    ),
                ),
                endpoint_url=str(settings.STORAGE_URL),
            ),
            partitioner_config=PartitionerConfig(
                partition_by_api=False,
                additional_partition_args={
                    "split_pdf_page": True,
                    "split_pdf_allow_failed": True,
                    "split_pdf_concurrency_level": 15,
                },
            ),
            chunker_config=ChunkerConfig(chunking_strategy="basic"),
            embedder_config=EmbedderConfig(
                embedding_provider="openai",
                embedding_model_name="text-embedding-3-small",
                embedding_api_key=settings.OPENAI_API_KEY,
            ),
            destination_connection_config=LocalWeaviateConnectionConfig(
                access_config=Secret(LocalWeaviateAccessConfig()),
            ),
            stager_config=LocalWeaviateUploadStagerConfig(),
            uploader_config=LocalWeaviateUploaderConfig(collection=collection_name),
        ).run()


async def upload_document_to_weaviate_v2(
    document: DocumentModel, collection_name: str
) -> None:
    """
    Usage:
        await upload_document_to_weaviate_v2(document, collection_name="Documents")
    """
    clear_contextvars()
    bind_contextvars(user_id=document.user_id, document_id=document.id)

    s3_client = boto3.client(
        "s3",
        endpoint_url=str(settings.STORAGE_URL),
        aws_access_key_id=settings.STORAGE_ACCESS_KEY.get_secret_value(),
        aws_secret_access_key=settings.STORAGE_SECRET_KEY.get_secret_value(),
        config=botocore.config.Config(signature_version="s3v4"),
    )

    file_buffer = io.BytesIO()
    s3_client.download_fileobj(
        Bucket=settings.STORAGE_BUCKET, Key=document.storage_path, Fileobj=file_buffer
    )
    logger.info("Partitioning the file...")
    elements = partition_pdf(
        file=file_buffer,
        strategy="hi_res",
        split_pdf_page=True,
        split_pdf_allow_failed=True,
        split_pdf_concurrency_level=15,
        infer_table_structure=True,
    )
    logger.info("Chunking the file...")
    chunks = dispatch.chunk(elements=elements, chunking_strategy="by_title")

    wvc = get_weaviate_client(with_openai=True)
    await wvc.connect()
    collection = wvc.collections.get(collection_name)

    record_id = uuid5(NAMESPACE_DNS, document.storage_path)
    await collection.data.delete_many(
        where=Filter.by_property("record_id").equal(str(record_id))
    )
    for batch in range(0, len(chunks), 100):
        chunk_batch = chunks[batch : batch + 100]
        objects = [
            {
                **_normalize(chunk.to_dict()),
                "record_id": record_id,
                "user_id": document.user_id,
            }
            for chunk in chunk_batch
        ]
        await collection.data.insert_many(objects)
    await wvc.close()
    logger.info("Document uploaded to Weaviate with {len(chunks)} chunks")


def _normalize(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        **chunk,
        "text": chunk["metadata"]["text_as_html"]
        if chunk["type"] == "Table" or chunk["type"] == "TableChunk"
        else chunk["text"],
        "type": chunk["type"],
        "element_id": chunk["element_id"],
        "metadata": {
            **chunk["metadata"],
            "filetype": chunk["metadata"]["filetype"],
            "page_number": str(chunk["metadata"]["page_number"]),
        },
    }
