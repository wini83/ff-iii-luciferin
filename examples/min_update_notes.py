"""Demonstrate minimal usage of :class:`FireflyClient`. editing notes"""

import asyncio
import logging

from settings_min import settings

from fireflyiii_enricher_core.api import FireflyClient, TransactionUpdate

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    logging.info("Updating transaction notes in Firefly III")
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4975  # Replace with your transaction ID
        response = await firefly.update_transaction(
            tx_id, TransactionUpdate(notes="Test notes#5\nTest notes#6")
        )
        print(response)
    finally:
        await firefly.close()


asyncio.run(main())
