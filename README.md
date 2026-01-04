# Firefly III Enricher Core 
[![Python package](https://github.com/wini83/fireflyiii-enricher-core/actions/workflows/python-package.yml/badge.svg)](https://github.com/wini83/fireflyiii-enricher-core/actions/workflows/python-package.yml) [![Pylint](https://github.com/wini83/fireflyiii-enricher-core/actions/workflows/pylint.yml/badge.svg)](https://github.com/wini83/fireflyiii-enricher-core/actions/workflows/pylint.yml)

A Python library for enriching Firefly III transactions by updating descriptions, notes, and tags.

## ✨ Features

- ✅ Fetch transactions from Firefly III API
- 📂 Fetch categories from Firefly III API
- 📝 Update transaction **descriptions** and **notes**
- 🏷️ Add tags to transactions
- 📝 Assign category
- 🚫 Filter uncategorized or single-part transactions
- ⚠️ Robust error handling (timeouts, connection issues, malformed responses)

## 📦 Installation

```bash
pip install git+https://github.com/wini83/fireflyiii-enricher-core.git
```

## 🧰 Requirements

- Python 3.12+
- `httpx`
- `python-dotenv` (optional, for loading environment variables from `.env`)

## ⚙️ Usage

### Environment Setup

```env
# .env file
FIREFLY_URL=https://your-firefly-instance/api
FIREFLY_TOKEN=your_access_token
```

### Minimal Example

```python
import asyncio
import os

from dotenv import load_dotenv

from fireflyiii_enricher_core.api import FireflyClient

load_dotenv()

async def main() -> None:
    client = FireflyClient(
        base_url=os.getenv("FIREFLY_URL"),
        token=os.getenv("FIREFLY_TOKEN")
    )
    try:
        # Fetch latest withdrawals
        transactions = await client.fetch_transactions()

        # Fetch categories
        categories = await client.fetch_categories()

        # Update description
        await client.update_transaction_description(123, "New description")

        # Update notes
        await client.update_transaction_notes(123, "Some extra notes")

        # Add a tag
        await client.add_tag_to_transaction(123, "processed")

        # assign category
        await client.assign_transaction_category(123, new_category_id=1)
    finally:
        await client.close()

asyncio.run(main())

```
Helper filters are also re-exported from `fireflyiii_enricher_core.api`.

## 🧪 Testing

### Install development dependencies

```bash
pip install -e .[dev]
```

### Run tests

```bash
pytest
```

### Linting

```bash
pylint $(git ls-files '*.py')
```

## 🛠 Development

- Use `.env` for secrets/tokens (not committed to version control)
- Follow PEP8 and naming conventions
- Keep public methods well-documented

## 📄 License

MIT License — see [`LICENSE`](LICENSE) for full text.
