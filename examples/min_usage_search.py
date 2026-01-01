"""Demonstrate minimal usage of :class:`FireflyClient`."""

import asyncio
import logging

from settings_min import settings

from fireflyiii_enricher_core.firefly_client import (
    FireflyClient,
    filter_by_description,
    filter_single_part,
    filter_without_category,
    filter_without_tag,
    simplify_transactions,
)

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=settings.firefly_url, token=settings.firefly_token)
    try:
        # Fetch, filter and simplify transactions
        logging.info("Fetching transactions from Firefly III")
        transactions = await firefly.fetch_transactions()
        logging.info("Filtering transactions")
        transactions = filter_single_part(transactions)
        transactions = filter_without_category(transactions)
        transactions = filter_by_description(transactions, "allegro", exact_match=False)
        allegro_amount = len(transactions)
        transactions = filter_without_tag(transactions, "allegro_done")
        simplified = simplify_transactions(transactions)
        logging.info(
            f"Transaction allegro: {allegro_amount} - not processed {len(simplified)}"
        )
        logging.info("Fetching categories from Firefly III")

        categories = await firefly.fetch_categories(simplified=True)

        logging.info(f"Fetched {len(categories)} categories")

    finally:
        await firefly.close()


asyncio.run(main())
