from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


@dataclass(eq=False)
class SimplifiedItem:
    date: date
    amount: Decimal

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimplifiedItem):
            return NotImplemented
        return self.date == other.date and abs(self.amount) == abs(other.amount)


class TxType(StrEnum):
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"


class AccountType(StrEnum):
    ASSET = "asset"
    EXPENSE = "expense"
    REVENUE = "revenue"
    LIABILITY = "liability"
    LOAN = "loan"
    DEBT = "debt"
    MORTGAGE = "mortgage"
    INITIAL_BALANCE = "initial-balance"
    RECONCILIATION = "reconciliation"


@dataclass(slots=True, frozen=True)
class Currency:
    code: str  # "EUR"
    symbol: str  # "€"
    decimals: int  # 2


@dataclass(slots=True, frozen=True)
class FXContext:
    original_currency: Currency
    original_amount: Decimal


@dataclass(slots=True, frozen=True)
class SimplifiedCategory:
    """Simplified representation of a Firefly III Category."""

    id: int
    name: str


@dataclass(slots=True, frozen=True)
class SimplifiedAccountRef:
    id: int
    name: str
    type: AccountType
    iban: str | None = None


@dataclass(eq=False)
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
    source_account: SimplifiedAccountRef | None = None
    destination_account: SimplifiedAccountRef | None = None
