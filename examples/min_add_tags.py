"""Demonstrate minimal usage of :class:`FireflyClient`. editing notes"""

import asyncio
import json
import logging

from settings_min import settings

from fireflyiii_enricher_core.api import FireflyClient

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4080  # Replace with your transaction ID
        logging.info("Adding tag to transaction in Firefly III")
        response = await firefly.add_tag_to_transaction(tx_id, "test tag#3")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    finally:
        await firefly.close()


asyncio.run(main())
