"""Unit tests for FireflyClient class."""

import asyncio
from typing import Any, Dict, Iterable, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ff_iii_luciferin.api import FireflyAPIError, FireflyClient
from ff_iii_luciferin.api.transaction_update import TransactionUpdate
from ff_iii_luciferin.domain.models import SimplifiedCategory, SimplifiedTx

BASE_URL = "https://demo.firefly.local"
TOKEN = "test-token"


def _transaction_split_payload(
    description: str,
    *,
    amount: str = "10.00",
    date: str = "2025-01-01T00:00:00+00:00",
    tags: List[str] | None = None,
    notes: str | None = None,
    category_id: str | None = None,
    category_name: str | None = None,
) -> Dict[str, Any]:
    return {
        "type": "withdrawal",
        "date": date,
        "amount": amount,
        "description": description,
        "source_id": "1",
        "destination_id": "2",
        "tags": tags or [],
        "notes": notes,
        "category_id": category_id,
        "category_name": category_name,
    }


def _transaction_read_payload(
    tx_id: str, split_payloads: Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "type": "transactions",
        "id": tx_id,
        "attributes": {"transactions": list(split_payloads)},
        "links": {"self": f"{BASE_URL}/api/v1/transactions/{tx_id}"},
    }


def _transaction_array_response(
    tx_ids: List[str], next_link: str | None
) -> Dict[str, Any]:
    splits = [_transaction_split_payload(f"tx-{tx_id}") for tx_id in tx_ids]
    data = [
        _transaction_read_payload(tx_id, [split])
        for tx_id, split in zip(tx_ids, splits, strict=False)
    ]
    return {
        "data": data,
        "meta": {"pagination": {"current_page": 1, "total_pages": 1}},
        "links": {"next": next_link},
    }


def _transaction_single_response(
    tx_id: str, split_payload: Dict[str, Any]
) -> Dict[str, Any]:
    return {"data": _transaction_read_payload(tx_id, [split_payload])}


def _category_read_payload(category_id: str, name: str) -> Dict[str, Any]:
    return {"type": "categories", "id": category_id, "attributes": {"name": name}}


def _category_array_response(
    category_ids: List[str],
    current_page: int,
    total_pages: int,
) -> Dict[str, Any]:
    data = [
        _category_read_payload(category_id, f"Category {category_id}")
        for category_id in category_ids
    ]
    return {
        "data": data,
        "meta": {
            "pagination": {"current_page": current_page, "total_pages": total_pages}
        },
    }


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_fetch_transactions(mock_request: MagicMock) -> None:
    """Test fetching paginated transactions."""
    mock_request.side_effect = [
        MockResponse(_transaction_array_response(["1", "2"], "some_url")),
        MockResponse(_transaction_array_response(["3"], None)),
    ]

    async def run() -> list[SimplifiedTx]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.fetch_transactions()
        finally:
            await client.close()

    result = asyncio.run(run())
    assert [tx.id for tx in result] == [1, 2, 3]
    assert [tx.description for tx in result] == ["tx-1", "tx-2", "tx-3"]


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_fetch_categories(mock_request: MagicMock) -> None:
    """Test fetching paginated categories."""
    mock_request.side_effect = [
        MockResponse(_category_array_response(["1", "2"], 1, 2)),
        MockResponse(_category_array_response(["3"], 2, 2)),
    ]

    async def run() -> list[SimplifiedCategory]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.fetch_categories()
        finally:
            await client.close()

    result = asyncio.run(run())
    assert [category.id for category in result] == [1, 2, 3]
    assert [category.name for category in result] == [
        "Category 1",
        "Category 2",
        "Category 3",
    ]


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_get_transaction_happy_path(mock_request: MagicMock) -> None:
    """Test fetching a single transaction by ID."""
    split = _transaction_split_payload(
        "Lunch", tags=["food"], notes="Receipt", category_name="Eating Out"
    )
    mock_request.return_value = MockResponse(_transaction_single_response("123", split))

    async def run() -> SimplifiedTx:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.get_transaction(123)
        finally:
            await client.close()

    result = asyncio.run(run())
    assert result.id == 123
    assert result.description == "Lunch"
    assert result.tags == ["food"]
    assert result.notes == "Receipt"
    assert result.category == "Eating Out"


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_get_transaction_multipart_raises(mock_request: MagicMock) -> None:
    """Test multipart transactions are rejected."""
    split_a = _transaction_split_payload("Part A", amount="5.00")
    split_b = _transaction_split_payload("Part B", amount="5.00")
    mock_request.return_value = MockResponse(
        {
            "data": _transaction_read_payload("123", [split_a, split_b]),
        }
    )

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.get_transaction(123)
        finally:
            await client.close()

    with pytest.raises(
        FireflyAPIError, match="Transaction 123 is multipart and not supported"
    ):
        asyncio.run(run())


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_get_transaction_invalid_dto_raises(mock_request: MagicMock) -> None:
    """Test invalid transaction DTOs are rejected."""
    split = _transaction_split_payload("Broken", amount="not-a-number")
    mock_request.return_value = MockResponse(_transaction_single_response("123", split))

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.get_transaction(123)
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="Transaction 123 could not be mapped"):
        asyncio.run(run())


@pytest.mark.parametrize(
    ("update", "expected_patch"),
    [
        (
            TransactionUpdate(description="Test description"),
            {"description": "Test description"},
        ),
        (
            TransactionUpdate(notes="New note"),
            {"notes": "New note"},
        ),
        (
            TransactionUpdate(tags=["processed", "reviewed"]),
            {"tags": ["processed", "reviewed"]},
        ),
        (
            TransactionUpdate(category_id=42),
            {"category_id": "42"},
        ),
    ],
)
@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_update_transaction_fields(
    mock_request: MagicMock,
    update: TransactionUpdate,
    expected_patch: Dict[str, Any],
) -> None:
    """Test updating single fields on a transaction."""
    updated = _transaction_split_payload(
        "Updated", tags=["processed"], notes="ok", category_name="Utilities"
    )
    mock_request.return_value = MockResponse(
        _transaction_single_response("123", updated)
    )

    async def run() -> SimplifiedTx:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.update_transaction(123, update)
        finally:
            await client.close()

    result = asyncio.run(run())
    assert result.id == 123
    assert result.description == "Updated"
    assert mock_request.call_args.kwargs["json"] == {
        "apply_rules": True,
        "fire_webhooks": True,
        "transactions": [expected_patch],
    }


class MockResponse:
    """Generic mock response for testing purposes."""

    def __init__(self, json_data: Dict[str, Any]) -> None:
        """Initialize with mock JSON data."""
        self._json = json_data
        self.status_code: int = 200

    def json(self) -> Dict[str, Any]:
        """Return mocked JSON content."""
        return self._json

    def raise_for_status(self) -> None:
        """Simulate successful response (does nothing)."""
        return
