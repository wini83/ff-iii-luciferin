# pylint: disable=duplicate-code
"""Demonstrate minimal usage of :class:`FireflyClient`."""

import asyncio
import os

from dotenv import load_dotenv

from fireflyiii_enricher_core.firefly_client import (
    FireflyClient,
    filter_single_part,
    filter_without_category,
    filter_without_tag,
    simplify_transactions,
)

# Load environment variables from .env.example file
load_dotenv()

FIREFLY_URL = os.getenv("FIREFLY_URL")
FIREFLY_TOKEN = os.getenv("FIREFLY_TOKEN")

if FIREFLY_URL is None or FIREFLY_TOKEN is None:
    raise RuntimeError("Missing FIREFLY_URL or FIREFLY_TOKEN in environment.")


async def main() -> None:
    # Initialize Firefly III client with credentials
    firefly = FireflyClient(base_url=FIREFLY_URL, token=FIREFLY_TOKEN)
    try:
        # Fetch, filter and simplify transactions
        transactions = await firefly.fetch_transactions()
        transactions = filter_single_part(transactions)
        transactions = filter_without_category(transactions)
        # transactions = filter_by_description(
        # transactions, "allegro", exact_match=False)
        allegro_amount = len(transactions)
        transactions = filter_without_tag(transactions, "allegro_done")
        simplified = simplify_transactions(transactions)

        categories = await firefly.fetch_categories(simplified=True)

        print(categories)

        print(
            f"Transaction allegro: {allegro_amount} - not processed {len(transactions)}"
        )

        # Display matching transactions
        for tx in simplified:
            print(
                f"{tx.id}: {tx.date} | {tx.amount} | "
                f"{tx.description} |{tx.tags} | |{tx.notes}"
            )
    finally:
        await firefly.close()


asyncio.run(main())
