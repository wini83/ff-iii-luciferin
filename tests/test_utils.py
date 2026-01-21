from decimal import Decimal

from ff_iii_luciferin.mappers.utils import parse_decimal, parse_int


def test_parse_int_variants() -> None:
    assert parse_int(None) is None
    assert parse_int(12) == 12
    assert parse_int("  34 ") == 34
    assert parse_int("") is None
    assert parse_int("not-a-number") is None
    assert parse_int(object()) is None


def test_parse_decimal_variants() -> None:
    assert parse_decimal(None) is None
    value = Decimal("1.23")
    assert parse_decimal(value) == value
    assert parse_decimal(5) == Decimal("5")
    assert parse_decimal(1.5) == Decimal("1.5")
    assert parse_decimal(" 2.50 ") == Decimal("2.50")
    assert parse_decimal("") is None
    assert parse_decimal("bad") is None
    assert parse_decimal(object()) is None
