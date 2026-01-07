from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List


@dataclass(eq=False)
class SimplifiedItem:
    date: date
    amount: Decimal

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimplifiedItem):
            return NotImplemented
        return self.date == other.date and abs(self.amount) == abs(other.amount)


@dataclass
class SimplifiedTx(SimplifiedItem):
    """Simplified representation of a Firefly III transaction."""

    id: int
    description: str
    tags: List[str]
    notes: str
    category: str


@dataclass
class SimplifiedCategory:
    """Simplified representation of a Firefly III Category."""

    id: int
    name: str
