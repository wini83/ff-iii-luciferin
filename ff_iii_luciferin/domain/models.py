from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


@dataclass(eq=False)
class SimplifiedItem:
    """Date and amount used for candidate matching.

    Equality compares the date and absolute amount. The amount's sign and
    every field added by subclasses are ignored; this is a candidate match,
    not proof that two records represent the same payment.

    Attributes:
        date: Transaction calendar date.
        amount: Transaction amount as a decimal value.
    """

    date: date
    amount: Decimal

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimplifiedItem):
            return NotImplemented
        return self.date == other.date and abs(self.amount) == abs(other.amount)


class TxType(StrEnum):
    """Supported simplified transaction types."""

    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"


class AccountType(StrEnum):
    """Account types recognized by the transaction mapper."""

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
    """Currency details needed to display an amount.

    Attributes:
        code: ISO currency code, such as ``"EUR"``.
        symbol: Display symbol, such as ``"€"``.
        decimals: Number of decimal places to display.
    """

    code: str  # "EUR"
    symbol: str  # "€"
    decimals: int  # 2


@dataclass(slots=True, frozen=True)
class FXContext:
    """Original foreign amount when Firefly III reports a conversion.

    Attributes:
        original_currency: Currency of the original amount.
        original_amount: Amount in that currency.
    """

    original_currency: Currency
    original_amount: Decimal


@dataclass(slots=True, frozen=True)
class SimplifiedCategory:
    """Category ID and name from Firefly III.

    Attributes:
        id: Firefly III category ID.
        name: Category name.
    """

    id: int
    name: str


@dataclass(slots=True, frozen=True)
class SystemInfo:
    """Version and environment information from ``get_about()``.

    All fields are optional because the endpoint's schema permits them to be
    absent.

    Attributes:
        version: Firefly III application version.
        api_version: API version reported by Firefly III.
        php_version: PHP runtime version.
        os: Server operating system.
        driver: Database driver name.
    """

    version: str | None
    api_version: str | None
    php_version: str | None
    os: str | None
    driver: str | None


@dataclass(slots=True, frozen=True)
class SimplifiedAccountRef:
    """Account reference attached to a transaction split.

    Attributes:
        id: Firefly III account ID.
        name: Account name.
        type: Mapped account type.
        iban: IBAN if present in the API response.
    """

    id: int
    name: str
    type: AccountType
    iban: str | None = None


@dataclass(eq=False)
class SimplifiedTx(SimplifiedItem):
    """Mapped single-split Firefly III transaction.

    Inherits ``date`` and ``amount`` from ``SimplifiedItem``. Equality uses
    only those two fields, comparing absolute amounts. Multipart groups cannot
    be represented by this model.

    Attributes:
        id: Firefly III transaction group ID.
        description: Split description.
        tags: Tag names reported by Firefly III.
        notes: Optional split notes.
        category: Mapped category, if both its ID and name are available.
        currency: Currency used for ``amount``.
        fx: Original foreign amount and currency, when available.
        type: Withdrawal, deposit, or transfer.
        source_account: Source account when its reference can be mapped.
        destination_account: Destination account when it can be mapped.
        external_id: External identifier supplied by Firefly III, if any.
    """

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
    external_id: str | None = None
