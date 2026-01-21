from dataclasses import dataclass


@dataclass
class TransactionUpdate:
    description: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    category_id: int | None = None
