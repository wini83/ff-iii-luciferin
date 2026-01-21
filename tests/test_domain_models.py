from datetime import date
from decimal import Decimal

from ff_iii_luciferin.domain.models import SimplifiedItem


def test_simplified_item_eq_non_item_returns_not_implemented() -> None:
    item = SimplifiedItem(date=date(2025, 1, 1), amount=Decimal("1.00"))
    assert item.__eq__("nope") is NotImplemented
