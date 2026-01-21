from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


@dataclass(eq=False)
class SimplifiedItem:
    date: date
    amount: Decimal

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimplifiedItem):
            return NotImplemented
        return self.date == other.date and abs(self.amount) == abs(other.amount)


class TxType(str, Enum):
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"


@dataclass(slots=True, frozen=True)
class Currency:
    code: str  # "EUR"
    symbol: str  # "€"
    decimals: int  # 2


@dataclass(slots=True, frozen=True)
class FXContext:
    original_currency: Currency
    original_amount: Decimal


@dataclass
class SimplifiedCategory:
    """Simplified representation of a Firefly III Category."""

    id: int
    name: str


@dataclass
class SimplifiedTx(SimplifiedItem):
    """Simplified representation of a Firefly III transaction."""

    id: int
    description: str
    tags: list[str]
    notes: str | None
    category: SimplifiedCategory | None
    currency: Currency
    fx: FXContext | None
    type: TxType
