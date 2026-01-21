from datetime import date
from decimal import Decimal

from ff_iii_luciferin.domain.models import (
    Currency,
    SimplifiedItem,
    SimplifiedTx,
    TxType,
)
from ff_iii_luciferin.services.basic_matcher import match


def test_match_returns_records_with_same_date_and_amount() -> None:
    tx = SimplifiedTx(
        id=1,
        description="Coffee",
        amount=Decimal("10.00"),
        date=date(2025, 1, 1),
        tags=[],
        notes="",
        category=None,
        currency=Currency(code="USD", symbol="$", decimals=2),
        fx=None,
        type=TxType.WITHDRAWAL,
    )
    records = [
        SimplifiedItem(date=date(2025, 1, 1), amount=Decimal("-10.00")),
        SimplifiedItem(date=date(2025, 1, 2), amount=Decimal("10.00")),
    ]

    result = match(tx, records)

    assert result == [records[0]]


def test_match_handles_multiple_candidates() -> None:
    tx = SimplifiedTx(
        id=2,
        description="Subscription",
        amount=Decimal("25.00"),
        date=date(2025, 2, 1),
        tags=["recurring"],
        notes="",
        category=None,
        currency=Currency(code="USD", symbol="$", decimals=2),
        fx=None,
        type=TxType.WITHDRAWAL,
    )
    records = [
        SimplifiedItem(date=date(2025, 2, 1), amount=Decimal("25.00")),
        SimplifiedItem(date=date(2025, 2, 1), amount=Decimal("-25.00")),
    ]

    result = match(tx, records)

    assert result == records
