"""Utility client for interacting with the Firefly III API."""

import logging
from datetime import date
from typing import Any, Iterable, List, Sequence

import httpx

from fireflyiii_enricher_core.domain.models import SimplifiedCategory, SimplifiedTx
from fireflyiii_enricher_core.mappers.category_mapper import map_category
from fireflyiii_enricher_core.mappers.transaction_mapper import map_transaction
from fireflyiii_enricher_core.openapi.openapi_client.models.category_array import (
    CategoryArray,
)
from fireflyiii_enricher_core.openapi.openapi_client.models.transaction_array import (
    TransactionArray,
)
from fireflyiii_enricher_core.openapi.openapi_client.models.transaction_single import (
    TransactionSingle,
)

logger = logging.getLogger(__name__)


class FireflyAPIError(RuntimeError):
    """Raised when Firefly III API calls fail."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def filter_without_category(
    transactions: Sequence[SimplifiedTx],
) -> List[SimplifiedTx]:
    """Filter out transactions that already have a category set."""
    return [tx for tx in transactions if not tx.category]


def filter_single_part(transactions: Sequence[SimplifiedTx]) -> List[SimplifiedTx]:
    """Return only transactions that have a single sub-transaction."""
    return list(transactions)


def filter_by_description(
    transactions: Sequence[SimplifiedTx],
    description_filter: str,
    exact_match: bool = True,
) -> List[SimplifiedTx]:
    """Match transactions whose description matches the filter."""
    filtered: List[SimplifiedTx] = []
    for tx in transactions:
        desc = tx.description
        if exact_match and desc.lower() == description_filter.lower():
            filtered.append(tx)
        elif not exact_match and description_filter.lower() in desc.lower():
            filtered.append(tx)
    return filtered


def filter_without_tag(
    transactions: Sequence[SimplifiedTx], tag: str
) -> List[SimplifiedTx]:
    """
    Filters out transactions that contain a specific tag.

    Iterates over a list of transactions and returns only those
    that do not include the given tag in their tags field.
    """
    filtered: List[SimplifiedTx] = []
    for tx in transactions:
        if tag not in tx.tags:
            filtered.append(tx)
    return filtered


def simplify_transactions(transactions: Iterable[SimplifiedTx]) -> List[SimplifiedTx]:
    """Return simplified transactions already expressed in the domain model."""
    return list(transactions)


class FireflyClient:
    """Minimal wrapper around the Firefly III REST API."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }
        self._client = httpx.AsyncClient(headers=self.headers, timeout=10.0)

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                raise FireflyAPIError(
                    "Failed to parse JSON response",
                    status_code=response.status_code,
                ) from exc

        except httpx.TimeoutException as exc:
            raise FireflyAPIError("Request timed out") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise FireflyAPIError(
                f"HTTP error: {exc}", status_code=status_code
            ) from exc
        except httpx.RequestError as exc:
            raise FireflyAPIError(f"Request failed: {exc}") from exc

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def fetch_transactions(
        self,
        tx_type: str = "withdrawal",
        limit: int = 1000,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> List[SimplifiedTx]:
        """Retrieve transactions of the given type."""
        url = f"{self.base_url}/api/v1/transactions"
        params: dict[str, Any] = {"limit": limit, "type": tx_type}
        if start_date:
            params["start"] = start_date.isoformat()
        if end_date:
            params["end"] = end_date.isoformat()
        page = 1
        transactions: List[SimplifiedTx] = []

        while True:
            params["page"] = page
            response = await self._request("get", url, params=params)
            data = TransactionArray.model_validate(response)
            for tx in data.data:
                try:
                    transactions.append(map_transaction(tx))
                except ValueError as exc:
                    logger.warning("Skipping transaction %s: %s", tx.id, exc)
            if not data.links.next:
                break
            page += 1
        return transactions

    async def fetch_categories(
        self, limit: int = 1000, simplified: bool = False
    ) -> List[SimplifiedCategory]:
        """Retrieve categories from Firefly III."""
        url = f"{self.base_url}/api/v1/categories"
        params: dict[str, Any] = {"limit": limit}
        page = 1
        categories: List[SimplifiedCategory] = []

        while True:
            params["page"] = page
            response = await self._request("get", url, params=params)
            data = CategoryArray.model_validate(response)
            categories.extend(map_category(category) for category in data.data)
            pagination = data.meta.pagination
            if pagination and pagination.current_page and pagination.total_pages:
                if pagination.current_page >= pagination.total_pages:
                    break
            elif not response.get("links", {}).get("next"):
                break
            page += 1
        return categories

    async def update_transaction_description(
        self, transaction_id: int, new_description: str
    ) -> SimplifiedTx:
        """Change the description field for a given transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        existing = TransactionSingle.model_validate(response)
        old_desc = existing.data.attributes.transactions[0].description
        if new_description in old_desc:
            raise RuntimeError("New data is identical to the current one.")
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"description": new_description}],
        }
        response_put = await self._request("put", url, json=payload)
        updated = TransactionSingle.model_validate(response_put)
        return map_transaction(updated.data)

    async def update_transaction_notes(
        self, transaction_id: int, new_notes: str
    ) -> SimplifiedTx:
        """Replace the notes for a given transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        existing = TransactionSingle.model_validate(response)
        old_notes = existing.data.attributes.transactions[0].notes or ""
        if new_notes in old_notes:
            raise RuntimeError("New data is identical to the current one.")
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"notes": new_notes}],
        }
        response_put = await self._request("put", url, json=payload)
        updated = TransactionSingle.model_validate(response_put)
        return map_transaction(updated.data)

    async def assign_transaction_category(
        self, transaction_id: int, new_category_id: int
    ) -> SimplifiedTx:
        """Assign a category to the specified transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        existing = TransactionSingle.model_validate(response)
        old_category = existing.data.attributes.transactions[0].category_id
        if old_category is not None and old_category == str(new_category_id):
            raise RuntimeError("New data is identical to the current one.")
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"category_id": str(new_category_id)}],
        }
        response_put = await self._request("put", url, json=payload)
        updated = TransactionSingle.model_validate(response_put)
        return map_transaction(updated.data)

    async def add_tag_to_transaction(
        self, transaction_id: int, new_tag: str
    ) -> SimplifiedTx:
        """Attach a tag to the specified transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        existing = TransactionSingle.model_validate(response)
        old_sub_transactions = existing.data.attributes.transactions
        if len(old_sub_transactions) != 1:
            raise RuntimeError("Transaction is not single part")
        old_sub_tx = old_sub_transactions[0]
        tags = list(old_sub_tx.tags or [])
        if new_tag not in tags:
            tags.append(new_tag)
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"tags": tags}],
        }
        response_put = await self._request("put", url, json=payload)
        updated = TransactionSingle.model_validate(response_put)
        return map_transaction(updated.data)
