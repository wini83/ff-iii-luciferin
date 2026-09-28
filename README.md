# ff-iii-luciferin

[![CI](https://github.com/wini83/ff-iii-luciferin/actions/workflows/ci.yml/badge.svg)](https://github.com/wini83/ff-iii-luciferin/actions/workflows/ci.yml)
![PyPI](https://img.shields.io/pypi/v/ff-iii-luciferin?include_prereleases)
![Python](https://img.shields.io/pypi/pyversions/ff-iii-luciferin?include_prereleases)
[![codecov](https://codecov.io/gh/wini83/ff-iii-luciferin/graph/badge.svg?token=SSWFZZT4J1)](https://codecov.io/gh/wini83/ff-iii-luciferin)

**ff-iii-luciferin** is an async Python client and a small set of domain helpers
for working with [Firefly III](https://www.firefly-iii.org/) transactions. It
fetches transactions and categories, exposes simplified models, and updates a
transaction's description, notes, tags, or category.

Python 3.12 or newer is required.

## Install

```bash
pip install ff-iii-luciferin
```

## Quickstart

Set `FIREFLY_URL` to the **instance root** (without `/api/v1`) and
`FIREFLY_TOKEN` to a personal access token. The client does not read environment
variables itself; this example passes them explicitly.

```python
import asyncio
import os

from ff_iii_luciferin.api import FireflyClient


async def main() -> None:
    client = FireflyClient(
        base_url=os.environ["FIREFLY_URL"],
        token=os.environ["FIREFLY_TOKEN"],
    )
    try:
        about = await client.get_about()
        print(f"Firefly III: {about.version}")

        transactions = await client.fetch_transactions(max_pages=1)
        for tx in transactions:
            print(tx.id, tx.date, tx.amount, tx.description, tx.external_id)

    finally:
        await client.close()


asyncio.run(main())
```

`fetch_transactions()` defaults to withdrawals; pass `tx_type` for
another Firefly III transaction type. Multipart and invalid transactions are
skipped during listing, while `get_transaction()` raises `FireflyAPIError` for
an unsupported multipart transaction.

## Documentation

The [full documentation](https://wini83.github.io/ff-iii-luciferin/) covers
setup, transaction updates, matching semantics, and the public API reference.
The OpenAPI-generated transport models are implementation details and are not
part of that reference.

## Local development

With Docker and Python 3 installed, start an isolated Firefly III demo and
run a read-only example:

```bash
bash scripts/demo/start.sh
set -a; source .firefly-demo/env; set +a
uv run python examples/min_usage_search.py
```

The demo listens on `http://127.0.0.1:18080` and seeds accounts, categories,
withdrawals, a deposit, and a transfer in SQLite. Repeated starts reuse the
data without duplicating seed records. `bash scripts/demo/stop.sh` stops the
container while keeping the database. `.firefly-demo/` contains a token and
app key; keep it private. New containers use `fireflyiii/core:latest`; set
`FIREFLY_DEMO_IMAGE=fireflyiii/core:version-6.7.4` to pin an image before the
first start. An existing container keeps its image until recreated.

To run the live test against an isolated instance, set `FIREFLY_E2E_URL` and
`FIREFLY_E2E_TOKEN`, then run `uv run pytest tests/test_firefly_e2e.py`.
Without those variables, the test is skipped. The GitHub Actions E2E workflow
starts its own disposable instance.

Build the documentation locally with:

```bash
uv sync --locked --group docs
uv run --group docs mkdocs build --strict
```

See [LICENSE](LICENSE) for the MIT license.
