"""Match bank transactions with records retrieved from Firefly."""

from collections.abc import Iterable

from fireflyiii_enricher_core.domain.models import SimplifiedItem, SimplifiedTx


def match(
    tx: SimplifiedTx,
    records: Iterable[SimplifiedItem],
) -> list[SimplifiedItem]:
    return [r for r in records if r == tx]


1
