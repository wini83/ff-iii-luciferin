from dataclasses import dataclass
from typing import Literal

from ff_iii_luciferin.domain.models import (
    Currency,
    FXContext,
    SimplifiedCategory,
    SimplifiedTx,
    TxType,
)
from ff_iii_luciferin.mappers.utils import parse_decimal, parse_int
from ff_iii_luciferin.openapi.openapi_client.models.transaction_read import (
    TransactionRead,
)
from ff_iii_luciferin.openapi.openapi_client.models.transaction_split import (
    TransactionSplit,
)
from ff_iii_luciferin.openapi.openapi_client.models.transaction_type_property import (
    TransactionTypeProperty,
)


@dataclass(frozen=True)
class TransactionMapResult:
    tx: SimplifiedTx | None
    reason: Literal["multipart", "invalid"] | None


def map_currency(split: TransactionSplit) -> Currency | None:
    if (
        not split.currency_code
        or not split.currency_symbol
        or split.currency_decimal_places is None
    ):
        return None

    return Currency(
        code=split.currency_code,
        symbol=split.currency_symbol,
        decimals=split.currency_decimal_places,
    )


def map_fx_context(split: TransactionSplit) -> FXContext | None:
    if not split.foreign_currency_code or not split.foreign_amount:
        return None

    foreign_amount = parse_decimal(split.foreign_amount)
    if foreign_amount is None:
        return None

    if (
        not split.foreign_currency_symbol
        or split.foreign_currency_decimal_places is None
    ):
        return None

    return FXContext(
        original_currency=Currency(
            code=split.foreign_currency_code,
            symbol=split.foreign_currency_symbol,
            decimals=split.foreign_currency_decimal_places,
        ),
        original_amount=foreign_amount,
    )


def map_tx_type(api_type: str) -> TxType | None:
    try:
        ff_type = TransactionTypeProperty(api_type)
    except ValueError:
        return None

    return {
        TransactionTypeProperty.WITHDRAWAL: TxType.WITHDRAWAL,
        TransactionTypeProperty.DEPOSIT: TxType.DEPOSIT,
        TransactionTypeProperty.TRANSFER: TxType.TRANSFER,
    }.get(ff_type)


def map_transaction(tx: TransactionRead) -> TransactionMapResult:
    attrs = tx.attributes
    assert attrs is not None

    splits = attrs.transactions
    if len(splits) != 1:
        return TransactionMapResult(tx=None, reason="multipart")

    split = splits[0]

    # --- data ---
    if split.var_date is None:
        return TransactionMapResult(tx=None, reason="invalid")

    tx_id = parse_int(tx.id)
    if tx_id is None:
        return TransactionMapResult(tx=None, reason="invalid")

    amount = parse_decimal(split.amount)
    if amount is None:
        return TransactionMapResult(tx=None, reason="invalid")

    # --- type ---
    tx_type = map_tx_type(split.type)
    if tx_type is None:
        return TransactionMapResult(tx=None, reason="invalid")

    # --- currency ---
    currency = map_currency(split)
    if currency is None:
        return TransactionMapResult(tx=None, reason="invalid")

    # --- category ---
    category = None
    if split.category_id and split.category_name:
        category_id = parse_int(split.category_id)
        if category_id is not None:
            category = SimplifiedCategory(
                id=category_id,
                name=split.category_name,
            )

    # --- FX ---
    fx = map_fx_context(split)

    simple_tx = SimplifiedTx(
        id=tx_id,
        type=tx_type,
        description=split.description,
        amount=amount,
        date=split.var_date.date(),
        tags=list(split.tags or []),
        notes=split.notes or None,
        category=category,
        currency=currency,
        fx=fx,
    )

    return TransactionMapResult(tx=simple_tx, reason=None)
