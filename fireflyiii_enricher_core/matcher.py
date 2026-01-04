"""Match bank transactions with records retrieved from Firefly."""

from typing import List

from fireflyiii_enricher_core.domain.models import SimplifiedItem, SimplifiedTx


# pylint: disable=too-few-public-methods
class TransactionMatcher:
    """Helper for aligning CSV records with Firefly transactions."""

    @staticmethod
    def match(tx: SimplifiedTx, records: List[SimplifiedItem]) -> List[SimplifiedItem]:
        """Return all records that match the given transaction."""
        matches: List[SimplifiedItem] = []
        for record in records:
            if record.compare(tx):
                matches.append(record)
        return matches
