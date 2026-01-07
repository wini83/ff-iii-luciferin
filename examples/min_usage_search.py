"""Demonstrate minimal usage of :class:`FireflyClient`. fetching transactions."""

import asyncio
import logging

from settings_min import settings

from ff_iii_luciferin.api import FireflyClient

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        transactions = await firefly.fetch_transactions()
        logging.info("Fetched %s transactions", len(transactions))
        for tx in transactions[:20]:
            logging.info(f"TX {tx.id} - {tx.amount} - {tx.date} ; {tx.description}, ")
    finally:
        await firefly.close()


asyncio.run(main())
