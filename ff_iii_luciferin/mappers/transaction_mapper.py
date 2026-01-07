from dataclasses import dataclass
from typing import Literal, Sequence

from ff_iii_luciferin.domain.models import SimplifiedTx
from ff_iii_luciferin.mappers.utils import parse_decimal, parse_int
from ff_iii_luciferin.openapi.openapi_client.models.transaction_read import (
    TransactionRead,
)
from ff_iii_luciferin.openapi.openapi_client.models.transaction_split import (
    TransactionSplit,
)


@dataclass(frozen=True)
class TransactionMapResult:
    tx: SimplifiedTx | None
    reason: Literal["multipart", "invalid"] | None


def map_transaction(tx: TransactionRead) -> TransactionMapResult:
    attrs = tx.attributes
    assert attrs is not None

    splits: Sequence[TransactionSplit] = attrs.transactions
    if len(splits) != 1:
        return TransactionMapResult(tx=None, reason="multipart")

    split = splits[0]

    if split.var_date is None:
        return TransactionMapResult(tx=None, reason="invalid")

    id = parse_int(tx.id)
    if id is None:
        return TransactionMapResult(tx=None, reason="invalid")

    amount = parse_decimal(split.amount)
    if amount is None:
        return TransactionMapResult(tx=None, reason="invalid")

    simple_tx = SimplifiedTx(
        id=id,
        description=split.description,
        amount=amount,
        date=split.var_date.date(),
        tags=list(split.tags or []),
        notes=split.notes or "",
        category=split.category_name or "",
    )

    return TransactionMapResult(tx=simple_tx, reason=None)
