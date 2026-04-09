from datetime import date
from decimal import Decimal

from ff_iii_luciferin.domain.models import (
    Currency,
    SimplifiedItem,
    SimplifiedTx,
    TxType,
)


def test_simplified_item_eq_non_item_returns_not_implemented() -> None:
    item = SimplifiedItem(date=date(2025, 1, 1), amount=Decimal("1.00"))
    assert item.__eq__("nope") is NotImplemented


def test_simplified_tx_eq_uses_simplified_item_logic() -> None:
    left = SimplifiedTx(
        id=1,
        description="one",
        amount=Decimal("10.00"),
        date=date(2025, 1, 1),
        tags=[],
        notes=None,
        category=None,
        currency=Currency(code="USD", symbol="$", decimals=2),
        fx=None,
        type=TxType.WITHDRAWAL,
    )
    right = SimplifiedTx(
        id=999,
        description="two",
        amount=Decimal("-10.00"),
        date=date(2025, 1, 1),
        tags=["x"],
        notes="different",
        category=None,
        currency=Currency(code="EUR", symbol="€", decimals=2),
        fx=None,
        type=TxType.DEPOSIT,
    )

    assert left == right


def test_simplified_tx_account_fields_default_to_none() -> None:
    tx = SimplifiedTx(
        id=1,
        description="one",
        amount=Decimal("10.00"),
        date=date(2025, 1, 1),
        tags=[],
        notes=None,
        category=None,
        currency=Currency(code="USD", symbol="$", decimals=2),
        fx=None,
        type=TxType.WITHDRAWAL,
    )

    assert tx.source_account is None
    assert tx.destination_account is None
