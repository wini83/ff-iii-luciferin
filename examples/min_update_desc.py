"""Demonstrate minimal usage of :class:`FireflyClient`. editing description"""

import asyncio
import json
import logging

from settings_min import settings

from fireflyiii_enricher_core.firefly_client import FireflyClient

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    logging.info("Starting minimal update description example")
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4975  # Replace with your transaction ID
        response = await firefly.update_transaction_description(
            tx_id, "BLIK - płatność w internecie"
        )
        print(json.dumps(response, indent=2, ensure_ascii=False))
    finally:
        await firefly.close()


asyncio.run(main())
