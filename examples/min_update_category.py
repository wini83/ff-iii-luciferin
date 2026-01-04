"""Demonstrate minimal usage of :class:`FireflyClient`. editing category"""

import asyncio
import logging

from settings_min import settings

from fireflyiii_enricher_core.api import FireflyClient, TransactionUpdate

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4080
        response = await firefly.update_transaction(
            tx_id, TransactionUpdate(category_id=2)
        )
        print(response)
    finally:
        await firefly.close()


asyncio.run(main())
