"""Behavior of the handwritten transaction helpers."""

import asyncio
from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import patch

from ff_iii_luciferin.api import FireflyClient
from ff_iii_luciferin.domain.models import Currency, SimplifiedTx, TxType
from ff_iii_luciferin.mappers.transaction_mapper import TransactionMapResult
from ff_iii_luciferin.services.transactions import (
    FetchTransactionsStats,
    build_add_tag_payload,
    fetch_transactions_with_stats,
)


def make_transaction() -> SimplifiedTx:
    return SimplifiedTx(
        date=date(2026, 9, 1),
        amount=Decimal("12.50"),
        id=123,
        description="Purchase",
        tags=["imported"],
        notes=None,
        category=None,
        currency=Currency(code="EUR", symbol="€", decimals=2),
        fx=None,
        type=TxType.WITHDRAWAL,
    )


def test_build_add_tag_payload_does_not_mutate_or_duplicate() -> None:
    tx = make_transaction()

    assert build_add_tag_payload(tx, "reviewed") == ["imported", "reviewed"]
    assert build_add_tag_payload(tx, "imported") == ["imported"]
    assert tx.tags == ["imported"]


def test_fetch_transactions_with_stats_counts_mapping_outcomes() -> None:
    tx = make_transaction()
    received: dict[str, Any] = {}

    async def results(
        self: FireflyClient, **kwargs: Any
    ) -> AsyncIterator[TransactionMapResult]:
        received.update(kwargs)
        yield TransactionMapResult(tx=tx, reason=None)
        yield TransactionMapResult(tx=None, reason="multipart")
        yield TransactionMapResult(tx=None, reason="invalid")

    async def run() -> tuple[list[SimplifiedTx], FetchTransactionsStats]:
        client = FireflyClient("https://firefly.example", "token")
        try:
            return await fetch_transactions_with_stats(
                client,
                tx_type="transfer",
                page_size=25,
                max_pages=2,
                start_date=date(2026, 9, 1),
                end_date=date(2026, 9, 30),
            )
        finally:
            await client.close()

    with patch.object(FireflyClient, "_iter_transaction_map_results", results):
        transactions, stats = asyncio.run(run())

    assert transactions == [tx]
    assert (stats.total, stats.multipart, stats.invalid) == (1, 1, 1)
    assert stats.duration_ms >= 0
    assert received == {
        "tx_type": "transfer",
        "page_size": 25,
        "max_pages": 2,
        "start_date": date(2026, 9, 1),
        "end_date": date(2026, 9, 30),
    }
