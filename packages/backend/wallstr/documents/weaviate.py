from urllib.parse import urlparse

import weaviate
from weaviate import WeaviateAsyncClient

from wallstr.conf import settings


def get_weaviate_client(with_openai: bool = False) -> WeaviateAsyncClient:
    if settings.WEAVIATE_API_URL and settings.WEAVIATE_GRPC_URL:
        api_url = urlparse(settings.WEAVIATE_API_URL.get_secret_value())
        grpc_url = urlparse(settings.WEAVIATE_GRPC_URL.get_secret_value())

        if not api_url.hostname:
            raise ValueError("WEAVIATE_API_URL must have a hostname")

        api_port = api_url.port
        if not api_port:
            api_port = 443 if api_url.scheme == "https" else 80

        if not grpc_url.hostname:
            raise ValueError("WEAVIATE_GRPC_URL must have a hostname")

        grpc_port = grpc_url.port
        if not grpc_port:
            grpc_port = 443 if grpc_url.scheme == "https" else 80

        client = weaviate.use_async_with_custom(
            http_host=api_url.hostname,
            http_port=api_port,
            http_secure=api_url.scheme == "https",
            grpc_host=grpc_url.hostname,
            grpc_port=grpc_port,
            grpc_secure=grpc_url.scheme == "https",
            headers={
                "X-OpenAI-Api-Key": settings.OPENAI_API_KEY.get_secret_value(),
            }
            if with_openai
            else None,
        )
        return client

    raise ValueError("WEAVIATE_API_URL, WEAVIATE_GRPC_URL are not set")
