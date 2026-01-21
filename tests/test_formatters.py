from decimal import Decimal

from ff_iii_luciferin.domain.formatters import format_amount


def test_format_amount_rounds_half_up() -> None:
    assert format_amount(Decimal("1.005"), 2) == "1.01"
    assert format_amount(Decimal("1.004"), 2) == "1.00"


def test_format_amount_handles_zero_decimals() -> None:
    assert format_amount(Decimal("12.5"), 0) == "13"


def test_format_amount_handles_negative_values() -> None:
    assert format_amount(Decimal("-2.345"), 2) == "-2.35"
