"""Match bank transactions with records retrieved from Firefly."""

from collections.abc import Iterable

from ff_iii_luciferin.domain.models import SimplifiedItem, SimplifiedTx


def match(
    tx: SimplifiedTx,
    records: Iterable[SimplifiedItem],
) -> list[SimplifiedItem]:
    """Find candidates with the same date and absolute amount.

    This uses ``SimplifiedItem`` equality. IDs, currency, description, tags,
    and external IDs are not checked. Review candidates before deduplication.

    Args:
        tx: Firefly III transaction to compare.
        records: Candidate items to scan once.

    Returns:
        Every matching item, preserving the input order.
    """
    return [r for r in records if r == tx]
