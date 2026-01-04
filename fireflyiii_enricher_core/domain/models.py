from dataclasses import dataclass
from datetime import date
from typing import Any, List


@dataclass(eq=False)
class SimplifiedItem:
    """Representation of a simplified transaction item."""

    date: date
    amount: float

    def compare_amount(self, amount: float) -> bool:
        """Return ``True`` if the amounts are equal ignoring their sign."""
        return abs(float(self.amount)) == abs(float(amount))

    def compare(self, other: Any) -> bool:
        """Return ``True`` if ``other`` has the same date and amount."""
        if not isinstance(other, SimplifiedItem):
            return False
        return self.date == other.date and self.compare_amount(other.amount)


@dataclass
class SimplifiedTx(SimplifiedItem):
    """Simplified representation of a Firefly III transaction."""

    id: str
    description: str
    tags: List[str]
    notes: str
    category: str


@dataclass
class SimplifiedCategory:
    """Simplified representation of a Firefly III Category."""

    id: str
    name: str

    @classmethod
    def from_api_dict(cls, category_raw: dict[str, Any]) -> "SimplifiedCategory":
        """Create instance of SimplifiedCategory from raw api dict"""
        category_id = category_raw.get("id", "")
        attributes = category_raw.get("attributes", {})
        name = attributes.get("name", "")
        return cls(id=category_id, name=name)
