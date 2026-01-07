from decimal import Decimal, InvalidOperation
from typing import Optional


def parse_int(value: object) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None
    return None


def parse_decimal(value: object) -> Optional[Decimal]:
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        # float -> str, żeby uniknąć binarnego syfu
        return Decimal(str(value))

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return Decimal(value)
        except InvalidOperation:
            return None

    return None
