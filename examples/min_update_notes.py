"""Demonstrate minimal usage of :class:`FireflyClient`. editing notes"""

import asyncio
import logging

from settings_min import settings

from ff_iii_luciferin.api import FireflyClient, TransactionUpdate

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    logging.info("Updating transaction notes in Firefly III")
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4975  # Replace with your transaction ID
        tx = await firefly.get_transaction(tx_id)
        logging.info("Current notes for %s: %s", tx.id, tx.notes)
        response = await firefly.update_transaction(
            tx_id, TransactionUpdate(notes="Test notes#5\nTest notes#6")
        )
        logging.info("Updated transaction %s notes.", response.id)
    finally:
        await firefly.close()


asyncio.run(main())
