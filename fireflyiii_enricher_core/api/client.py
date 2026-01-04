"""Utility client for interacting with the Firefly III API."""

import logging
from datetime import date
from typing import Any, List

import httpx

from fireflyiii_enricher_core.api.transaction_update import TransactionUpdate
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

    async def get_transaction(self, transaction_id: int) -> SimplifiedTx:
        """
        Fetch a single transaction by ID and return it as a domain model.
        """
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"

        response = await self._request("get", url)
        dto = TransactionSingle.model_validate(response)

        return map_transaction(dto.data)

    async def update_transaction(
        self, transaction_id: int, update: TransactionUpdate
    ) -> SimplifiedTx:
        """Update selected fields for a given transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        split_update: dict[str, Any] = {}
        if update.description is not None:
            split_update["description"] = update.description
        if update.notes is not None:
            split_update["notes"] = update.notes
        if update.tags is not None:
            split_update["tags"] = list(update.tags)
        if update.category_id is not None:
            split_update["category_id"] = str(update.category_id)
        if not split_update:
            raise ValueError("Transaction update payload is empty.")
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [split_update],
        }
        response_put = await self._request("put", url, json=payload)
        updated = TransactionSingle.model_validate(response_put)
        return map_transaction(updated.data)
