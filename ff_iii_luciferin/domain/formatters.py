from decimal import ROUND_HALF_UP, Decimal


def format_amount(amount: Decimal, decimals: int) -> str:
    """Round an amount for display using decimal half-up rounding.

    Args:
        amount: Decimal amount to format.
        decimals: Number of digits after the decimal point.

    Returns:
        Rounded decimal string without a currency symbol.
    """
    quant = Decimal("1").scaleb(-decimals)
    return str(amount.quantize(quant, rounding=ROUND_HALF_UP))
