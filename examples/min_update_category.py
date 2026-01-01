# pylint: disable=duplicate-code
"""Demonstrate minimal usage of :class:`FireflyClient`. editing notes"""

import asyncio
import json
import os

from dotenv import load_dotenv

from fireflyiii_enricher_core.firefly_client import FireflyClient

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
        tx_id = 4080
        response = await firefly.assign_transaction_category(tx_id, new_category_id=2)
        print(json.dumps(response, indent=2, ensure_ascii=False))
    finally:
        await firefly.close()


asyncio.run(main())
