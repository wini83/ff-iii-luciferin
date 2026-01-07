# ff-iii-luciferin

**ff-iii-luciferin** is a Python enrichment engine for  
[Firefly III](https://www.firefly-iii.org/) transactions.

It provides a clean, async-first API for post-processing financial data:
descriptions, notes, tags, and categories — without polluting your domain logic.

---

## ✨ Key Features

- 🔌 Async client for Firefly III API (built on `httpx`)
- 📝 Update transaction **descriptions** and **notes**
- 🏷️ Add or manage **tags**
- 🗂️ Assign or change **categories**
- 🚫 Filter unwanted transactions (e.g. uncategorized, split-only)
- ⚠️ Explicit handling of API, network, and data errors
- 🧱 Generated OpenAPI client kept internal (not public API)

---

## 📦 Installation

From PyPI:

````bash
pip install ff-iii-luciferin
````

Python **3.12+** required.

---

## ⚙️ Configuration

The client requires access to your Firefly III instance and a personal access token.

Provide them via environment variables:

````env
FIREFLY_URL=https://your-firefly-instance/api
FIREFLY_TOKEN=your_access_token
````

Using `python-dotenv` is optional but recommended for local development.

---

## 🚀 Quick Start

Minimal async example:

````python
import asyncio
import os

from ff_iii_luciferin.api import FireflyClient


async def main() -> None:
    client = FireflyClient(
        base_url=os.environ["FIREFLY_URL"],
        token=os.environ["FIREFLY_TOKEN"],
    )

    try:
        transactions = await client.fetch_transactions()
        categories = await client.fetch_categories()

        await client.update_transaction_description(
            transaction_id=123,
            description="Updated description",
        )

        await client.update_transaction_notes(
            transaction_id=123,
            notes="Additional notes",
        )

        await client.add_tag_to_transaction(
            transaction_id=123,
            tag="processed",
        )

        await client.assign_transaction_category(
            transaction_id=123,
            new_category_id=1,
        )
    finally:
        await client.close()


asyncio.run(main())
````

## 📄 License

MIT License.  

See the `LICENSE` file for details.
