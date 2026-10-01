# Getting started

Install Python 3.12 or newer and the package:

```bash
pip install ff-iii-luciferin
```

Create a personal access token in Firefly III. Pass the instance root as
`FIREFLY_URL`, without `/api/v1`, and the token as `FIREFLY_TOKEN`. The library
does not load these environment variables automatically.

```python
import asyncio
import os

from ff_iii_luciferin.api import FireflyClient


async def main() -> None:
    client = FireflyClient(os.environ["FIREFLY_URL"], os.environ["FIREFLY_TOKEN"])
    try:
        about = await client.get_about()
        print("Firefly III version:", about.version)

        transactions = await client.fetch_transactions(max_pages=1)
        for tx in transactions:
            print(tx.id, tx.date, tx.amount, tx.description, tx.external_id)

        categories = await client.fetch_categories()
        print("Categories:", len(categories))
    finally:
        await client.close()


asyncio.run(main())
```

`fetch_transactions()` defaults to withdrawals. Supply `tx_type="transfer"`
or `tx_type="deposit"` when those are needed, or `tx_type="all"` to request all
types from Firefly III. The returned list still includes only supported
single-split transactions; see [Transactions and matching](transactions.md)
for the mapping limits. `max_pages=1` limits the example
to one API page; omit it to follow pagination until the last page. You can also
pass `start_date` and `end_date` as Python `date` values.

## Update an existing transaction

The following code **changes** the transaction with ID `123` in Firefly III:

```python
from ff_iii_luciferin.api import TransactionUpdate

updated = await client.update_transaction(
    123,
    TransactionUpdate(
        description="Corrected description",
        notes="Checked against the receipt",
        tags=["reviewed", "receipt"],
        category_id=7,
    ),
)
```

`TransactionUpdate` accepts any non-empty combination of those four fields.
Passing `tags` replaces the transaction's tag list; it does not append one tag.
To preserve existing tags, read the transaction and build the new list first:

```python
from ff_iii_luciferin.services.transactions import build_add_tag_payload

current = await client.get_transaction(123)
updated = await client.update_transaction(
    current.id,
    TransactionUpdate(tags=build_add_tag_payload(current, "reviewed")),
)
```

The update examples assume `client` was created and will be closed as in the
first example. HTTP, timeout, response parsing, and mapping errors are raised
as `FireflyAPIError`; HTTP errors expose a `status_code` attribute.

## Local Firefly III demo

To experiment without changing your own ledger, run the repository's Docker
demo from the repository root:

```bash
bash scripts/demo/start.sh
set -a; source .firefly-demo/env; set +a
uv run python examples/min_usage_search.py
```

The script seeds a SQLite-backed demo at `http://127.0.0.1:18080` and reuses
its data on subsequent starts. Stop it with `bash scripts/demo/stop.sh`.
Credentials in `.firefly-demo/` must remain private. The edit examples in the
repository use hardcoded transaction IDs; select an ID from the search output
before running one.
