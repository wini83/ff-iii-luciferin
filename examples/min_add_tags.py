"""Demonstrate minimal usage of :class:`FireflyClient`. editing notes"""

import asyncio
import logging

from settings_min import settings

from fireflyiii_enricher_core.api import FireflyClient
from fireflyiii_enricher_core.api.transaction_update import TransactionUpdate
from fireflyiii_enricher_core.services.transactions import build_add_tag_payload

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4080  # Replace with your transaction ID
        logging.info("Fetching transaction from Firefly III")
        tx = await firefly.get_transaction(tx_id)
        logging.info("Adding tag to transaction in Firefly III")
        tags = build_add_tag_payload(tx, "test tag#3")
        payload = TransactionUpdate(tags=tags)
        response = await firefly.update_transaction(tx_id, payload)
        print(response)
    finally:
        await firefly.close()


asyncio.run(main())
