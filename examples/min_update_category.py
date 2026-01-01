"""Demonstrate minimal usage of :class:`FireflyClient`. editing category"""

import asyncio
import json
import logging

from settings_min import settings

from fireflyiii_enricher_core.firefly_client import FireflyClient

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        tx_id = 4080
        response = await firefly.assign_transaction_category(tx_id, new_category_id=2)
        print(json.dumps(response, indent=2, ensure_ascii=False))
    finally:
        await firefly.close()


asyncio.run(main())
