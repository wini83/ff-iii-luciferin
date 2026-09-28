# Transactions and matching

`fetch_transactions()` and `get_transaction()` return `SimplifiedTx`, a
handwritten domain model with a `Decimal` amount, `date`, type, category,
currency, optional account references, optional FX context, tags, notes, and
the Firefly III `external_id`. The `external_id` is `None` when Firefly III
does not supply one.

Firefly III returns transaction groups containing one or more splits. This
client maps only groups with **exactly one split**. The list method logs and
skips multipart or invalid groups; the single-transaction method raises
`FireflyAPIError` when a group cannot be mapped. Fetching categories returns
`SimplifiedCategory` objects. `get_about()` returns a `SystemInfo` object.

## Matching by date and amount

`SimplifiedItem` and its subclass `SimplifiedTx` compare equal when their
dates and **absolute amounts** match. Other fields, including IDs,
descriptions, tags, and `external_id`, do not affect that equality. This is a
candidate lookup, not a guarantee that two bank records are the same payment.

```python
from datetime import date
from decimal import Decimal

from ff_iii_luciferin.domain.models import SimplifiedItem
from ff_iii_luciferin.services.basic_matcher import match

candidates = [
    SimplifiedItem(date=date(2026, 9, 1), amount=Decimal("-12.50")),
    SimplifiedItem(date=date(2026, 9, 2), amount=Decimal("12.50")),
]
matches = match(tx, candidates)  # tx is a previously fetched SimplifiedTx
```

`match()` returns every candidate with the same date and absolute amount.
Inspect additional details before changing or deduplicating transactions.

For counts of mapped, multipart, and invalid transaction groups, use
`fetch_transactions_with_stats()` from
`ff_iii_luciferin.services.transactions`. It returns the transactions and a
`FetchTransactionsStats` value.
