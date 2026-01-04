"""Demonstrate minimal usage of :class:`FireflyClient`."""

import asyncio
import logging

from settings_min import settings

from fireflyiii_enricher_core.api import FireflyClient

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        # Fetch, filter and simplify transactions
        logging.info("Fetching transactions from Firefly III")
        transactions = await firefly.fetch_transactions()
        logging.info("Filtering transactions")
        transactions = [tx for tx in transactions if not tx.category]
        transactions = [
            tx for tx in transactions if "allegro" in tx.description.lower()
        ]
        allegro_amount = len(transactions)
        transactions = [tx for tx in transactions if "allegro_done" not in tx.tags]
        simplified = list(transactions)
        logging.info(
            f"Transaction allegro: {allegro_amount} - not processed {len(simplified)}"
        )
        if len(simplified) > 0:
            logging.info("Listing all unprocessed transactions:")
            for tx in simplified:
                logging.info(f" {tx.id} - {tx.date} {tx.description}  ({tx.amount}) ")
            return
        logging.info("Fetching categories from Firefly III")

        categories = await firefly.fetch_categories(simplified=True)

        logging.info(f"Fetched {len(categories)} categories")

    finally:
        await firefly.close()


asyncio.run(main())
