"""Unit tests for FireflyClient class."""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fireflyiii_enricher_core.firefly_client import FireflyAPIError, FireflyClient

BASE_URL = "https://demo.firefly.local"
TOKEN = "test-token"


@patch(
    "fireflyiii_enricher_core.firefly_client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_fetch_transactions(mock_request: MagicMock) -> None:
    """Test fetching paginated transactions."""
    mock_request.side_effect = [
        MockResponse(
            {"data": [{"id": "1"}, {"id": "2"}], "links": {"next": "some_url"}}
        ),
        MockResponse({"data": [{"id": "3"}], "links": {"next": None}}),
    ]

    async def run() -> list[dict[str, Any]]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.fetch_transactions()
        finally:
            await client.close()

    result = asyncio.run(run())
    assert len(result) == 3


@patch(
    "fireflyiii_enricher_core.firefly_client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_fetch_categories(mock_request: MagicMock) -> None:
    """Test fetching paginated categories."""
    mock_request.side_effect = [
        MockResponse(
            {"data": [{"id": "1"}, {"id": "2"}], "links": {"next": "some_url"}}
        ),
        MockResponse({"data": [{"id": "3"}], "links": {"next": None}}),
    ]

    async def run() -> list[dict[str, Any]]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.fetch_categories()
        finally:
            await client.close()

    result = asyncio.run(run())
    assert len(result) == 3


@patch(
    "fireflyiii_enricher_core.firefly_client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_update_description_success(mock_request: MagicMock) -> None:
    """Test successful update of transaction description."""
    mock_request.side_effect = [MockResponse({}), MockResponse({})]

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.update_transaction_description(123, "Test")
        finally:
            await client.close()

    asyncio.run(run())


@patch(
    "fireflyiii_enricher_core.firefly_client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_update_transaction_notes_success(mock_request: MagicMock) -> None:
    """Test successful update of transaction notes."""
    mock_request.side_effect = [MockResponse({}), MockResponse({})]

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.update_transaction_notes(123, "Some note")
        finally:
            await client.close()

    asyncio.run(run())


@patch(
    "fireflyiii_enricher_core.firefly_client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_add_tag_to_transaction(mock_request: MagicMock) -> None:
    """Test successful adding of a tag to a transaction."""
    mock_response_data = {
        "data": {
            "attributes": {
                "transactions": [{"description": "Old description", "tags": []}]
            }
        }
    }
    mock_request.side_effect = [MockResponse(mock_response_data), MockResponse({})]

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.add_tag_to_transaction(123, "processed")
        finally:
            await client.close()

    asyncio.run(run())


@patch(
    "fireflyiii_enricher_core.firefly_client.httpx.AsyncClient.request",
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
    "fireflyiii_enricher_core.firefly_client.httpx.AsyncClient.request",
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
