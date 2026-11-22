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

## Fetching transaction types

`fetch_transactions()` defaults to `tx_type="withdrawal"`. To request every
transaction type from Firefly III in one paginated call, pass `tx_type="all"`:

```python
transactions = await client.fetch_transactions(tx_type="all")
```

With no `max_pages` or date range, the client follows all API pages without
restricting the dates. The returned `SimplifiedTx` list can contain
withdrawals, deposits, and transfers. It is **not a complete snapshot of every
Firefly III transaction group**: the mapper skips groups with multiple splits,
other transaction types (such as opening balances and reconciliations), and
groups with invalid or missing data. To measure those omissions, use
`fetch_transactions_with_stats(client, tx_type="all")` from
`ff_iii_luciferin.services.transactions`; its `multipart` and `invalid`
counters report the skipped groups. The returned transaction list still
contains only successfully mapped groups.

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


## Reconciliation state

`SimplifiedTx.reconciled` preserves Firefly III's split reconciliation flag:
`True`, `False`, or `None` when omitted. `transaction_journal_id` identifies the
single split; `id` remains the transaction **group** ID.

Use the existing update method to set or clear the flag:

```python
from ff_iii_luciferin.api import TransactionUpdate

updated = await client.update_transaction(
    tx.id,
    TransactionUpdate(reconciled=True),
    apply_rules=False,
    fire_webhooks=False,
)
assert updated.reconciled is True
```

`reconciled=False` clears the flag. `None` leaves it unchanged and is not sent
in the request. Firefly III documents reconciled amounts as protected from
editing. The flag records a verification decision; it does not compare bank
statements, verify balances, or create a balancing transaction.

Rules and webhooks remain enabled by default for backward compatibility. Disable
them explicitly for status-only updates when you do not want those automations.

Every non-empty update now reads the current group before writing. Unsupported
multipart or invalid groups are rejected before any PUT request. A valid journal
ID is required and is included in the patch to identify the intended split.
This adds one GET request per update, but does not provide an atomic lock:
concurrent changes or server-side rules may still affect the result. Multipart
updates remain unsupported.
