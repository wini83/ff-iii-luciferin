"""Unit tests for FireflyClient class."""

import asyncio
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Literal
from unittest.mock import AsyncMock, MagicMock, call, patch

import httpx
import pytest

from ff_iii_luciferin.api import (
    FireflyAPIError,
    FireflyClient,
    SimplifiedAccount,
    SystemInfo,
)
from ff_iii_luciferin.api.transaction_update import TransactionUpdate
from ff_iii_luciferin.domain.models import (
    Currency,
    SimplifiedCategory,
    SimplifiedTx,
    TxType,
)
from ff_iii_luciferin.mappers.transaction_mapper import TransactionMapResult

BASE_URL = "https://demo.firefly.local"
TOKEN = "test-token"


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_get_about(mock_request: MagicMock) -> None:
    mock_request.return_value = MockResponse(
        {
            "data": {
                "version": "6.7.4",
                "api_version": "6.7.4",
                "php_version": "8.3.0",
                "os": "Linux",
                "driver": "sqlite",
            }
        }
    )

    async def run() -> SystemInfo:
        client = FireflyClient(BASE_URL + "/", TOKEN)
        try:
            return await client.get_about()
        finally:
            await client.close()

    assert asyncio.run(run()) == SystemInfo(
        version="6.7.4",
        api_version="6.7.4",
        php_version="8.3.0",
        os="Linux",
        driver="sqlite",
    )
    mock_request.assert_awaited_once_with("get", f"{BASE_URL}/api/v1/about")


@pytest.mark.parametrize("payload", [{}, {"data": None}, {"data": {"version": 123}}])
@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_get_about_invalid_response(
    mock_request: MagicMock, payload: dict[str, Any]
) -> None:
    mock_request.return_value = MockResponse(payload)

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.get_about()
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="system information"):
        asyncio.run(run())


def _account_payload(account_id: str, **attributes: Any) -> dict[str, Any]:
    return {
        "type": "accounts",
        "id": account_id,
        "attributes": {
            "name": f"Account {account_id}",
            "type": "expense",
            **attributes,
        },
    }


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_fetch_accounts_paginates_and_maps_bank_details(
    mock_request: MagicMock,
) -> None:
    iban = "GB98MIDL07009312345678"
    mock_request.side_effect = [
        MockResponse(
            {
                "data": [_account_payload("1", iban=iban, active=False)],
                "meta": {"pagination": {"current_page": 1, "total_pages": 2}},
            }
        ),
        MockResponse(
            {
                "data": [_account_payload("2", account_number="00123", active=False)],
                "meta": {"pagination": {"current_page": 2, "total_pages": 2}},
            }
        ),
    ]

    async def run() -> list[SimplifiedAccount]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.fetch_accounts(
                account_type="expense", active=False, limit=1
            )
        finally:
            await client.close()

    assert asyncio.run(run()) == [
        SimplifiedAccount(1, "Account 1", "expense", iban=iban, active=False),
        SimplifiedAccount(
            2, "Account 2", "expense", account_number="00123", active=False
        ),
    ]
    assert mock_request.await_args_list == [
        call(
            "get",
            f"{BASE_URL}/api/v1/accounts",
            params={"limit": 1, "page": page, "type": "expense", "active": False},
        )
        for page in (1, 2)
    ]


@pytest.mark.parametrize(
    ("account_type", "details"),
    [
        ("expense", {"iban": "GB98MIDL07009312345678", "account_number": "00123"}),
        ("revenue", {}),
    ],
)
@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_create_account_returns_account_id(
    mock_request: MagicMock,
    account_type: Literal["expense", "revenue"],
    details: dict[str, str],
) -> None:
    mock_request.return_value = MockResponse(
        {
            "data": _account_payload(
                "42", name="Counterparty", type=account_type, **details
            )
        }
    )

    async def run() -> SimplifiedAccount:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.create_account(
                name="Counterparty", account_type=account_type, **details
            )
        finally:
            await client.close()

    assert asyncio.run(run()) == SimplifiedAccount(
        42, "Counterparty", account_type, active=True, **details
    )
    mock_request.assert_awaited_once_with(
        "post",
        f"{BASE_URL}/api/v1/accounts",
        json={"name": "Counterparty", "type": account_type, **details},
    )


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_fetch_accounts_without_filters_uses_next_link(mock_request: MagicMock) -> None:
    mock_request.side_effect = [
        MockResponse(
            {"data": [_account_payload("1")], "meta": {}, "links": {"next": "?page=2"}}
        ),
        MockResponse({"data": [_account_payload("2")], "meta": {}}),
    ]

    async def run() -> list[SimplifiedAccount]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.fetch_accounts()
        finally:
            await client.close()

    assert [account.id for account in asyncio.run(run())] == [1, 2]
    assert mock_request.await_args_list == [
        call("get", f"{BASE_URL}/api/v1/accounts", params={"limit": 50, "page": page})
        for page in (1, 2)
    ]


@pytest.mark.parametrize(
    ("operation", "response", "error"),
    [
        ("list", {"data": []}, "Invalid response schema for account array"),
        ("create", {"data": None}, "Invalid response schema for account"),
        ("create", {"data": _account_payload("invalid")}, "Invalid account ID"),
    ],
)
@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_account_endpoints_reject_invalid_responses(
    mock_request: MagicMock, operation: str, response: dict[str, Any], error: str
) -> None:
    mock_request.return_value = MockResponse(response)

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            if operation == "list":
                await client.fetch_accounts()
            else:
                await client.create_account(name="Counterparty", account_type="expense")
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match=error):
        asyncio.run(run())


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_create_account_rejects_unsupported_type(mock_request: MagicMock) -> None:
    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.create_account(
                name="Checking",
                account_type="asset",  # type: ignore[arg-type]
            )
        finally:
            await client.close()

    with pytest.raises(ValueError, match="Account type must be expense or revenue"):
        asyncio.run(run())
    mock_request.assert_not_awaited()


def _transaction_split_payload(
    description: str,
    *,
    amount: str = "10.00",
    date: str = "2025-01-01T00:00:00+00:00",
    tags: list[str] | None = None,
    notes: str | None = None,
    category_id: str | None = None,
    category_name: str | None = None,
    currency_code: str = "USD",
    currency_symbol: str = "$",
    currency_decimals: int = 2,
) -> dict[str, Any]:
    return {
        "type": "withdrawal",
        "transaction_journal_id": "456",
        "date": date,
        "amount": amount,
        "description": description,
        "source_id": "1",
        "destination_id": "2",
        "tags": tags or [],
        "notes": notes,
        "category_id": category_id,
        "category_name": category_name,
        "currency_code": currency_code,
        "currency_symbol": currency_symbol,
        "currency_decimal_places": currency_decimals,
    }


def _transaction_read_payload(
    tx_id: str, split_payloads: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "type": "transactions",
        "id": tx_id,
        "attributes": {"transactions": list(split_payloads)},
        "links": {"self": f"{BASE_URL}/api/v1/transactions/{tx_id}"},
    }


def _transaction_array_response(
    tx_ids: list[str], next_link: str | None
) -> dict[str, Any]:
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
    tx_id: str, split_payload: dict[str, Any]
) -> dict[str, Any]:
    return {"data": _transaction_read_payload(tx_id, [split_payload])}


def _category_read_payload(category_id: str, name: str) -> dict[str, Any]:
    return {"type": "categories", "id": category_id, "attributes": {"name": name}}


def _category_array_response(
    category_ids: list[str],
    current_page: int,
    total_pages: int,
) -> dict[str, Any]:
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
        "Lunch",
        tags=["food"],
        notes="Receipt",
        category_id="4",
        category_name="Eating Out",
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
    assert result.category == SimplifiedCategory(id=4, name="Eating Out")


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
        (TransactionUpdate(reconciled=True), {"reconciled": True}),
        (TransactionUpdate(reconciled=False), {"reconciled": False}),
        (TransactionUpdate(source_id=17), {"source_id": "17"}),
        (TransactionUpdate(destination_id=29), {"destination_id": "29"}),
    ],
)
@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_update_transaction_fields(
    mock_request: MagicMock,
    update: TransactionUpdate,
    expected_patch: dict[str, Any],
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
    assert mock_request.await_count == 2
    assert mock_request.await_args_list[0] == call(
        "get", f"{BASE_URL}/api/v1/transactions/123"
    )
    assert mock_request.call_args.kwargs["json"] == {
        "apply_rules": True,
        "fire_webhooks": True,
        "transactions": [{**expected_patch, "transaction_journal_id": "456"}],
    }


def test_update_transaction_empty_payload_raises() -> None:
    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.update_transaction(123, TransactionUpdate())
        finally:
            await client.close()

    with pytest.raises(ValueError, match="Transaction update payload is empty"):
        asyncio.run(run())


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_request_json_parse_error(mock_request: MagicMock) -> None:
    mock_request.return_value = MockBadJsonResponse()

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client._request("get", f"{BASE_URL}/broken")
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="Failed to parse JSON response") as exc:
        asyncio.run(run())
    assert exc.value.status_code == 200


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_request_timeout_error(mock_request: MagicMock) -> None:
    request = httpx.Request("GET", f"{BASE_URL}/timeout")
    mock_request.side_effect = httpx.ReadTimeout("timeout", request=request)

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client._request("get", f"{BASE_URL}/timeout")
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="Request timed out: GET") as exc:
        asyncio.run(run())
    assert exc.value.status_code is None


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_request_http_status_error(mock_request: MagicMock) -> None:
    request = httpx.Request("GET", f"{BASE_URL}/status")
    response = httpx.Response(503, request=request)
    mock_request.side_effect = httpx.HTTPStatusError(
        "boom", request=request, response=response
    )

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client._request("get", f"{BASE_URL}/status")
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="HTTP error:") as exc:
        asyncio.run(run())
    assert exc.value.status_code == 503


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_request_request_error(mock_request: MagicMock) -> None:
    request = httpx.Request("GET", f"{BASE_URL}/boom")
    mock_request.side_effect = httpx.RequestError("boom", request=request)

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client._request("get", f"{BASE_URL}/boom")
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError, match="Request failed:") as exc:
        asyncio.run(run())
    assert exc.value.status_code is None


def test_fetch_transactions_skips_invalid_and_multipart() -> None:
    tx = SimplifiedTx(
        id=1,
        description="ok",
        amount=Decimal("1.00"),
        date=datetime(2025, 1, 1).date(),
        tags=[],
        notes=None,
        category=None,
        currency=Currency(code="USD", symbol="$", decimals=2),
        fx=None,
        type=TxType.WITHDRAWAL,
    )

    async def _gen(self: FireflyClient, **_: Any) -> Any:
        yield TransactionMapResult(tx=tx, reason=None)
        yield TransactionMapResult(tx=None, reason="multipart")
        yield TransactionMapResult(tx=None, reason="invalid")

    async def run() -> list[SimplifiedTx]:
        with patch.object(FireflyClient, "_iter_transaction_map_results", _gen):
            client = FireflyClient(BASE_URL, TOKEN)
            try:
                return await client.fetch_transactions()
            finally:
                await client.close()

    result = asyncio.run(run())
    assert result == [tx]


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_iter_transactions_honors_max_pages(mock_request: MagicMock) -> None:
    async def run() -> list[TransactionMapResult]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return [
                result
                async for result in client._iter_transaction_map_results(max_pages=0)
            ]
        finally:
            await client.close()

    result = asyncio.run(run())
    assert result == []
    mock_request.assert_not_called()


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_iter_transactions_empty_page_breaks(mock_request: MagicMock) -> None:
    mock_request.return_value = MockResponse(_transaction_array_response([], None))

    async def run() -> list[TransactionMapResult]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return [result async for result in client._iter_transaction_map_results()]
        finally:
            await client.close()

    result = asyncio.run(run())
    assert result == []
    assert mock_request.call_count == 1


@patch(
    "ff_iii_luciferin.api.client.httpx.AsyncClient.request",
    new_callable=AsyncMock,
)
def test_iter_transactions_includes_start_end_params(
    mock_request: MagicMock,
) -> None:
    mock_request.return_value = MockResponse(_transaction_array_response([], None))
    start = date(2025, 1, 2)
    end = date(2025, 1, 3)

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            async for _ in client._iter_transaction_map_results(
                start_date=start, end_date=end
            ):
                pass
        finally:
            await client.close()

    asyncio.run(run())
    params = mock_request.call_args.kwargs["params"]
    assert params["start"] == "2025-01-02"
    assert params["end"] == "2025-01-03"


def test_fetch_categories_uses_links_when_pagination_missing() -> None:
    category_1 = SimpleNamespace(id="1", attributes=SimpleNamespace(name="Cat 1"))
    category_2 = SimpleNamespace(id="2", attributes=SimpleNamespace(name="Cat 2"))

    async def run() -> list[SimplifiedCategory]:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            with (
                patch.object(
                    client,
                    "_request",
                    AsyncMock(
                        side_effect=[
                            {"links": {"next": "next"}},
                            {"links": {}},
                        ]
                    ),
                ),
                patch(
                    "ff_iii_luciferin.api.client.validate_response_category_array",
                    side_effect=[
                        SimpleNamespace(
                            data=[category_1],
                            meta=SimpleNamespace(pagination=None),
                        ),
                        SimpleNamespace(
                            data=[category_2],
                            meta=SimpleNamespace(pagination=None),
                        ),
                    ],
                ),
            ):
                return await client.fetch_categories()
        finally:
            await client.close()

    result = asyncio.run(run())
    assert [category.id for category in result] == [1, 2]


class MockResponse:
    """Generic mock response for testing purposes."""

    def __init__(self, json_data: dict[str, Any]) -> None:
        """Initialize with mock JSON data."""
        self._json = json_data
        self.status_code: int = 200

    def json(self) -> dict[str, Any]:
        """Return mocked JSON content."""
        return self._json

    def raise_for_status(self) -> None:
        """Simulate successful response (does nothing)."""
        return


class MockBadJsonResponse:
    """Mock response that fails JSON parsing."""

    status_code = 200

    def json(self) -> dict[str, Any]:
        raise ValueError("invalid json")

    def raise_for_status(self) -> None:
        return


@pytest.mark.parametrize("state", [True, False])
@pytest.mark.parametrize(
    "apply_rules,fire_webhooks", [(False, False), (True, False), (False, True)]
)
@patch("ff_iii_luciferin.api.client.httpx.AsyncClient.request", new_callable=AsyncMock)
def test_update_reconciliation_round_trip(
    mock_request: MagicMock, state: bool, apply_rules: bool, fire_webhooks: bool
) -> None:
    before = _transaction_split_payload("Invoice", notes="Keep notes", tags=["booked"])
    before["reconciled"] = not state
    after = {**before, "reconciled": state}
    mock_request.side_effect = [
        MockResponse(_transaction_single_response("123", before)),
        MockResponse(_transaction_single_response("123", after)),
    ]

    async def run() -> SimplifiedTx:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            return await client.update_transaction(
                123,
                TransactionUpdate(reconciled=state),
                apply_rules=apply_rules,
                fire_webhooks=fire_webhooks,
            )
        finally:
            await client.close()

    result = asyncio.run(run())
    assert result.reconciled is state
    assert result.notes == "Keep notes"
    assert result.tags == ["booked"]
    assert mock_request.await_args_list == [
        call("get", f"{BASE_URL}/api/v1/transactions/123"),
        call(
            "put",
            f"{BASE_URL}/api/v1/transactions/123",
            json={
                "apply_rules": apply_rules,
                "fire_webhooks": fire_webhooks,
                "transactions": [
                    {"transaction_journal_id": "456", "reconciled": state}
                ],
            },
        ),
    ]


@pytest.mark.parametrize(
    "invalid", ["multipart", "invalid", "missing_journal", "http_error"]
)
@patch("ff_iii_luciferin.api.client.httpx.AsyncClient.request", new_callable=AsyncMock)
def test_update_rejects_unsupported_current_transaction_before_put(
    mock_request: MagicMock, invalid: str
) -> None:
    split = _transaction_split_payload("Invoice")
    if invalid == "missing_journal":
        split.pop("transaction_journal_id")
    if invalid == "invalid":
        split.pop("currency_symbol")
    splits = [split, split] if invalid == "multipart" else [split]
    mock_request.return_value = MockResponse(
        {"data": _transaction_read_payload("123", splits)}
    )
    if invalid == "http_error":
        mock_request.side_effect = httpx.ConnectError("unavailable")

    async def run() -> None:
        client = FireflyClient(BASE_URL, TOKEN)
        try:
            await client.update_transaction(123, TransactionUpdate(reconciled=True))
        finally:
            await client.close()

    with pytest.raises(FireflyAPIError):
        asyncio.run(run())
    mock_request.assert_awaited_once_with("get", f"{BASE_URL}/api/v1/transactions/123")
