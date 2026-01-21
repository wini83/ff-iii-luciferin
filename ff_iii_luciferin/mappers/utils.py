from decimal import Decimal, InvalidOperation


def parse_int(value: object) -> int | None:
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


def parse_decimal(value: object) -> Decimal | None:
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
