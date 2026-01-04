from typing import Sequence

from fireflyiii_enricher_core.domain.models import SimplifiedTx
from fireflyiii_enricher_core.openapi.openapi_client.models.transaction_read import (
    TransactionRead,
)
from fireflyiii_enricher_core.openapi.openapi_client.models.transaction_split import (
    TransactionSplit,
)


def map_transaction(tx: TransactionRead) -> SimplifiedTx:
    attrs = tx.attributes
    assert attrs is not None

    splits: Sequence[TransactionSplit] = attrs.transactions
    if len(splits) != 1:
        raise ValueError("Only single-part transactions are supported")

    split = splits[0]

    return SimplifiedTx(
        id=tx.id,
        description=split.description,
        amount=float(split.amount),
        date=split.var_date.date(),
        tags=list(split.tags or []),
        notes=split.notes or "",
        category=split.category_name or "",
    )
