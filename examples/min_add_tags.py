"""Demonstrate minimal usage of :class:`FireflyClient`. adding a tag"""

import asyncio
import logging

from settings_min import settings

from fireflyiii_enricher_core.api import FireflyClient, TransactionUpdate

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4080  # Replace with your transaction ID
        tx = await firefly.get_transaction(tx_id)
        new_tags = [*tx.tags, "test-tag"]
        payload = TransactionUpdate(tags=new_tags)
        response = await firefly.update_transaction(tx_id, payload)
        logging.info("Updated transaction %s tags: %s", response.id, response.tags)
    finally:
        await firefly.close()


asyncio.run(main())
