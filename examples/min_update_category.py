"""Demonstrate minimal usage of :class:`FireflyClient`. editing category"""

import asyncio
import logging

from settings_min import settings

from ff_iii_luciferin.api import FireflyClient, TransactionUpdate

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4080
        tx = await firefly.get_transaction(tx_id)
        logging.info("Current category for %s: %s", tx.id, tx.category)
        response = await firefly.update_transaction(
            tx_id, TransactionUpdate(category_id=2)
        )
        logging.info(
            "Updated transaction %s category: %s", response.id, response.category
        )
    finally:
        await firefly.close()


asyncio.run(main())
