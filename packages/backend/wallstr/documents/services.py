import io
from datetime import timedelta
from uuid import NAMESPACE_DNS, UUID, uuid5

import boto3
import botocore.config
from redis.asyncio import Redis
from sqlalchemy import or_, sql
from sqlalchemy.ext.asyncio import AsyncSession
from weaviate.classes.query import Filter

from wallstr.conf import settings
from wallstr.core.llm import get_llm, get_llm_with_vision
from wallstr.documents.models import DocumentModel, DocumentStatus, DocumentType
from wallstr.documents.pdf_parser import PdfParser
from wallstr.documents.schemas import DocumentStatusSSE
from wallstr.documents.weaviate import get_weaviate_client
from wallstr.models.base import utc_now
from wallstr.services import BaseService


class DocumentService(BaseService):
    def __init__(self, db_session: AsyncSession, redis: Redis | None = None) -> None:
        super().__init__(db_session)

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=str(settings.STORAGE_URL),
            aws_access_key_id=settings.STORAGE_ACCESS_KEY.get_secret_value(),
            aws_secret_access_key=settings.STORAGE_SECRET_KEY.get_secret_value(),
            config=botocore.config.Config(signature_version="s3v4"),
        )
        self.redis = redis

    async def get_document(self, document_id: UUID) -> DocumentModel | None:
        async with self.tx():
            result = await self.db.execute(
                sql.select(DocumentModel).filter_by(id=document_id)
            )
        return result.scalar_one_or_none()

    def generate_upload_url(
        self, user_id: UUID, document: DocumentModel, error: str | None = None
    ) -> str:
        if user_id != document.user_id:
            raise ValueError("User is not the owner of the document")

        url = self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.STORAGE_BUCKET,
                "Key": document.storage_path,
            },
            ExpiresIn=60 * 5,
        )
        return url

    async def mark_document_uploaded(
        self, user_id: UUID, document_id: UUID
    ) -> DocumentModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(DocumentModel)
                .filter_by(
                    id=document_id,
                    user_id=user_id,
                    status=DocumentStatus.UPLOADING,
                )
                .values(status=DocumentStatus.UPLOADED, error=None, errored_at=None)
                .returning(DocumentModel)
            )
        document = result.scalar_one()
        await self._notify_document_status(document)
        return document

    async def mark_document_processing(
        self, user_id: UUID, document_id: UUID
    ) -> DocumentModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(DocumentModel)
                .filter_by(id=document_id, user_id=user_id)
                .where(
                    or_(
                        DocumentModel.status == DocumentStatus.UPLOADED,
                        DocumentModel.status == DocumentStatus.PROCESSING,
                        DocumentModel.status == DocumentStatus.READY,
                    )
                )
                .values(status=DocumentStatus.PROCESSING, error=None, errored_at=None)
                .returning(DocumentModel)
            )
        document = result.scalar_one()
        await self._notify_document_status(document)
        return document

    async def mark_document_ready(
        self, user_id: UUID, document_id: UUID
    ) -> DocumentModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(DocumentModel)
                .filter_by(
                    id=document_id, user_id=user_id, status=DocumentStatus.PROCESSING
                )
                .values(status=DocumentStatus.READY, error=None, errored_at=None)
                .returning(DocumentModel)
            )
        document = result.scalar_one()
        await self._notify_document_status(document)
        return document

    async def mark_document_errored(
        self, document_id: UUID, error: dict[str, str]
    ) -> DocumentModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(DocumentModel)
                .filter_by(id=document_id)
                .values(error=error, errored_at=utc_now())
                .returning(DocumentModel)
            )
        document = result.scalar_one()
        await self._notify_document_status(document)
        return document

    async def parse_document(self, document_id: UUID) -> DocumentModel:
        async with self.tx():
            document = await self.get_document(document_id)

            if not document:
                raise ValueError("Document not found")

            if document.doc_type != DocumentType.PDF:
                raise ValueError(f"Document type not supported: {document.doc_type}")

            if document.status == DocumentStatus.UPLOADING:
                raise Exception("Document is uploading")

            if not document.can_parse:
                raise Exception(
                    "Document cannot be processed, it is being processed already"
                )

            await self.mark_document_processing(document.user_id, document.id)

        try:
            file_buffer = io.BytesIO()
            self.s3_client.download_fileobj(
                Bucket=settings.STORAGE_BUCKET,
                Key=document.storage_path,
                Fileobj=file_buffer,
            )

            parser_cls = get_parser_cls(document.doc_type)
            llm = get_llm("gpt-4o")
            llm_with_vision = get_llm_with_vision()
            parser = parser_cls(llm, llm_with_vision)

            chunks = await parser.parse(file_buffer)
            record_id = uuid5(NAMESPACE_DNS, document.storage_path)
            for chunk in chunks:
                chunk["record_id"] = record_id
                chunk["user_id"] = document.user_id
                chunk["document_id"] = document.id
                chunk["version"] = PdfParser.version
                chunk["inference_model"] = PdfParser.inference_model

            # Put data to weaviate
            collection_name = "Documents"
            wvc = get_weaviate_client(with_openai=True)
            await wvc.connect()
            try:
                tenant_id = str(document.user_id)
                collection = wvc.collections.get(collection_name)
                if await collection.tenants.get_by_names([tenant_id]):
                    await collection.with_tenant(tenant_id).data.delete_many(
                        where=Filter.by_property("record_id").equal(str(record_id))
                    )
                for batch in range(0, len(chunks), 100):
                    objects = chunks[batch : batch + 100]
                    await collection.with_tenant(tenant_id).data.insert_many(objects)
            except Exception:
                raise
            finally:
                await wvc.close()
        except Exception as e:
            document = await self.mark_document_errored(
                document.id, {"message": str(e), "code": "parse_error"}
            )
            raise
        else:
            document = await self.mark_document_ready(document.user_id, document.id)
        return document

    async def _notify_document_status(self, document: DocumentModel) -> None:
        topic = f"{document.user_id}:documents:{document.id}"
        if self.redis is not None:
            await self.redis.publish(
                topic,
                DocumentStatusSSE(
                    id=document.id,
                    status=document.status,
                    updated_at=utc_now(),
                    error="Processing error" if document.error else None,
                    errored_at=document.errored_at,
                ).model_dump_json(),
            )


def get_parser_cls(doc_type: DocumentType) -> type[PdfParser]:
    if doc_type == DocumentType.PDF:
        return PdfParser
    raise ValueError(f"Document type not supported: {doc_type}")
