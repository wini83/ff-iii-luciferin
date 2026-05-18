# ff-iii-luciferin

[![CI](https://github.com/wini83/ff-iii-luciferin/actions/workflows/ci.yml/badge.svg)](https://github.com/wini83/ff-iii-luciferin/actions/workflows/ci.yml)
![PyPI](https://img.shields.io/pypi/v/ff-iii-luciferin?include_prereleases)
![Python](https://img.shields.io/pypi/pyversions/ff-iii-luciferin?include_prereleases)
![License](https://img.shields.io/pypi/l/ff-iii-luciferin?include_prereleases)
[![codecov](https://codecov.io/gh/wini83/ff-iii-luciferin/graph/badge.svg?token=SSWFZZT4J1)](https://codecov.io/gh/wini83/ff-iii-luciferin)

**ff-iii-luciferin** is a Python enrichment engine for  
[Firefly III](https://www.firefly-iii.org/) transactions.


Recent branch updates add richer transaction enrichment and a more readable
transaction search example:

- source and destination account references are now preserved on simplified transactions
- the search demo renders a compact table with `rich`
- the generated OpenAPI client has been refreshed for Firefly III API v6.5.5

It provides a clean, async-first API for post-processing financial data:
descriptions, notes, tags, and categories — without polluting your domain logic.

---

## ✨ Key Features

- 🔌 Async client for Firefly III API (built on `httpx`)
- 📝 Update transaction **descriptions** and **notes**
- 🏷️ Add or manage **tags**
- 🗂️ Assign or change **categories**
- 🏦 Preserve simplified **source/destination account** references
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

The `examples/min_usage_search.py` script shows the current transaction search
output with a `rich` table, including category and account columns.

## 📄 License

MIT License.  

MIT License — see [LICENSE](LICENSE) for details.
