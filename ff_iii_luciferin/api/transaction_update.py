from dataclasses import dataclass


@dataclass
class TransactionUpdate:
    """Fields accepted by ``FireflyClient.update_transaction()``.

    Supply at least one field. ``None`` means leave a field unchanged; an
    empty tag list removes all tags. A supplied tag list replaces the entire
    existing list rather than adding to it.

    Attributes:
        description: Replacement description.
        notes: Replacement notes; an empty string clears existing notes.
        tags: Complete replacement list of tag names.
        category_id: Firefly III category ID to assign.
    """

    description: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    category_id: int | None = None
