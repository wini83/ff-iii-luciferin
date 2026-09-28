import time
from dataclasses import dataclass
from datetime import date

from ff_iii_luciferin.api import FireflyClient
from ff_iii_luciferin.domain.models import SimplifiedTx


def build_add_tag_payload(
    tx: SimplifiedTx,
    tag: str,
) -> list[str]:
    """Build a replacement tag list with one tag added if missing.

    The returned list is independent of ``tx.tags`` and preserves its order.
    Pass it as ``TransactionUpdate(tags=...)`` to avoid replacing all existing
    tags with just the new one.

    Args:
        tx: Transaction whose current tags should be retained.
        tag: Tag name to add.

    Returns:
        A new list containing the original tags and, if needed, ``tag``.
    """
    tags = list(tx.tags)

    if tag not in tags:
        tags.append(tag)

    return tags


@dataclass
class FetchTransactionsStats:
    """Mapping counts and elapsed time for a transaction fetch.

    Attributes:
        total: Successfully mapped transaction groups.
        multipart: Groups skipped because they contain multiple splits.
        invalid: Groups skipped because mapping failed.
        duration_ms: Elapsed time in whole milliseconds.
    """

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
    """Fetch transactions while counting skipped groups.

    Accepts the same filters as ``FireflyClient.fetch_transactions()``. The
    returned list contains only successfully mapped single-split groups.

    Args:
        client: Open Firefly III client.
        tx_type: Firefly III transaction type filter.
        page_size: Requested groups per API page.
        max_pages: Maximum pages, or ``None`` to follow all pages.
        start_date: Inclusive start date, if supplied.
        end_date: Inclusive end date, if supplied.

    Returns:
        A pair of mapped transactions and mapping statistics.

    Raises:
        FireflyAPIError: A request fails or an API page has an invalid schema.
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
