import time
from dataclasses import dataclass
from datetime import date
from typing import List

from ff_iii_luciferin.api import FireflyClient
from ff_iii_luciferin.domain.models import SimplifiedTx


def build_add_tag_payload(
    tx: SimplifiedTx,
    tag: str,
) -> List[str]:
    tags = list(tx.tags)

    if tag not in tags:
        tags.append(tag)

    return tags


@dataclass
class FetchTransactionsStats:
    total: int = 0
    multipart: int = 0
    invalid: int = 0
    duration_ms: int = 0


async def fetch_transactions_with_stats(
    client: FireflyClient,
    *,
    tx_type: str = "withdrawal",
    page_size: int = 1000,
    max_pages: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[SimplifiedTx], FetchTransactionsStats]:
    """
    Fetch transactions and collect mapping statistics.
    """
    stats = FetchTransactionsStats()
    transactions: list[SimplifiedTx] = []
    start_ts = time.monotonic()

    async for result in client._iter_transaction_map_results(
        tx_type=tx_type,
        page_size=page_size,
        max_pages=max_pages,
        start_date=start_date,
        end_date=end_date,
    ):
        if result.tx is not None:
            transactions.append(result.tx)
            stats.total += 1
        elif result.reason == "multipart":
            stats.multipart += 1
        else:
            stats.invalid += 1
    stats.duration_ms = int((time.monotonic() - start_ts) * 1000)

    return transactions, stats
