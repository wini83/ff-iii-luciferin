"""Unit tests for FireflyClient class."""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fireflyiii_enricher_core.api.client import FireflyAPIError, FireflyClient
from fireflyiii_enricher_core.domain.models import SimplifiedCategory

BASE_URL = "https://demo.firefly.local"
TOKEN = "test-token"


def _transaction_split_payload(
    description: str,
    tags: List[str] | None = None,
    notes: str | None = None,
    category_id: str | None = None,
    category_name: str | None = None,
) -> Dict[str, Any]:
    return {
        "type": "withdrawal",
        "date": "2025-01-01T00:00:00+00:00",
        "amount": "10.00",
        "description": description,
        "source_id": None,
        "destination_id": None,
        "tags": tags or [],
        "notes": notes,
        "category_id": category_id,
        "category_name": category_name,
    }


def _transaction_read_payload(
    tx_id: str, split_payload: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "type": "transactions",
        "id": tx_id,
        "attributes": {"transactions": [split_payload]},
        "links": {},
    }


def _transaction_array_response(
    tx_ids: List[str], next_link: str | None
) -> Dict[str, Any]:
    splits = [_transaction_split_payload(f"tx-{tx_id}") for tx_id in tx_ids]
    data = [
        _transaction_read_payload(tx_id, split)
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
    return {"data": _transaction_read_payload(tx_id, split_payload)}


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
    "fireflyiii_enricher_core.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_fetch_transactions(mock_request: MagicMock) -> None:
    """Test fetching paginated transactions."""
    mock_request.side_effect = [
        MockResponse(_transaction_array_response(["1", "2"], "some_url")),
        MockResponse(_transaction_array_response(["3"], None)),
    ]

    async def run() -> list[Any]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.fetch_transactions()
        finally:
            await client.close()

    result = asyncio.run(run())
    assert len(result) == 3


@patch(
    "fireflyiii_enricher_core.api.client.httpx.AsyncClient.request",
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
    assert len(result) == 3


@patch(
    "fireflyiii_enricher_core.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_update_description_success(mock_request: MagicMock) -> None:
    """Test successful update of transaction description."""
    original = _transaction_split_payload("Old description")
    updated = _transaction_split_payload("Test")
    mock_request.side_effect = [
        MockResponse(_transaction_single_response("123", original)),
        MockResponse(_transaction_single_response("123", updated)),
    ]

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.update_transaction_description(123, "Test")
        finally:
            await client.close()

    asyncio.run(run())


@patch(
    "fireflyiii_enricher_core.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_update_transaction_notes_success(mock_request: MagicMock) -> None:
    """Test successful update of transaction notes."""
    original = _transaction_split_payload("Old description", notes="Old note")
    updated = _transaction_split_payload("Old description", notes="Some note")
    mock_request.side_effect = [
        MockResponse(_transaction_single_response("123", original)),
        MockResponse(_transaction_single_response("123", updated)),
    ]

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.update_transaction_notes(123, "Some note")
        finally:
            await client.close()

    asyncio.run(run())


@patch(
    "fireflyiii_enricher_core.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_add_tag_to_transaction(mock_request: MagicMock) -> None:
    """Test successful adding of a tag to a transaction."""
    original = _transaction_split_payload("Old description", tags=[])
    updated = _transaction_split_payload("Old description", tags=["processed"])
    mock_request.side_effect = [
        MockResponse(_transaction_single_response("123", original)),
        MockResponse(_transaction_single_response("123", updated)),
    ]

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.add_tag_to_transaction(123, "processed")
        finally:
            await client.close()

    asyncio.run(run())


@patch(
    "fireflyiii_enricher_core.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_timeout_handling(mock_request: MagicMock) -> None:
    """Test timeout exception is handled and re-raised."""
    import httpx

    mock_request.side_effect = httpx.TimeoutException("timeout")

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.fetch_transactions()
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="Request timed out"):
        asyncio.run(run())


@patch(
    "fireflyiii_enricher_core.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_json_decode_error(mock_request: MagicMock) -> None:
    """Test JSON decode error is handled gracefully."""

    class BadJsonResponse:
        """Mocked response that raises ValueError on json()."""

        status_code = 200

        def raise_for_status(self) -> None:
            """Mocked response that raises ValueError on json()."""
            return

        def json(self) -> Dict[str, Any]:
            """Mocked response that raises ValueError on json()."""
            raise ValueError("bad json")

    mock_request.return_value = BadJsonResponse()

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.fetch_transactions()
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="Failed to parse JSON response"):
        asyncio.run(run())


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
