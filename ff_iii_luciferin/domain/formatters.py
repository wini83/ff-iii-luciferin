from decimal import ROUND_HALF_UP, Decimal


def format_amount(amount: Decimal, decimals: int) -> str:
    quant = Decimal("1").scaleb(-decimals)
    return str(amount.quantize(quant, rounding=ROUND_HALF_UP))
