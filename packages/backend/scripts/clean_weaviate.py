# /usr/bin/env python
import asyncio

import structlog

from wallstr.documents.weaviate import get_weaviate_client
from wallstr.logging import configure_logging

configure_logging(name="clean_weaviate")

logger = structlog.get_logger()


async def migrate_weaviate() -> None:
    logger.info("Clean Weaviate")
    wvc = get_weaviate_client()
    await wvc.connect()

    logger.info("Deleting Documents collection")
    await wvc.collections.delete("Documents")

    logger.info("Deleting Prompts collection")
    await wvc.collections.delete("Prompts")

    await wvc.close()
    logger.info("Clean Weaviate done")


if __name__ == "__main__":
    asyncio.run(migrate_weaviate())
