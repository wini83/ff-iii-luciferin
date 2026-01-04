"""Demonstrate minimal usage of :class:`FireflyClient`. editing description"""

import asyncio
import logging

from settings_min import settings

from fireflyiii_enricher_core.api import FireflyClient, TransactionUpdate

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    logging.info("Starting minimal update description example")
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4975  # Replace with your transaction ID
        response = await firefly.update_transaction(
            tx_id, TransactionUpdate(description="BLIK - płatność w internecie")
        )
        print(response)
    finally:
        await firefly.close()


asyncio.run(main())
