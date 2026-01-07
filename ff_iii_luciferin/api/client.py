"""Utility client for interacting with the Firefly III API."""

import logging
from datetime import date
from typing import Any, AsyncIterator, List

import httpx

from ff_iii_luciferin.api.errors import FireflyAPIError
from ff_iii_luciferin.api.transaction_update import TransactionUpdate
from ff_iii_luciferin.api.validators import (
    validate_response_category_array,
    validate_response_single_tx,
    validate_response_transaction_array,
)
from ff_iii_luciferin.domain.models import SimplifiedCategory, SimplifiedTx
from ff_iii_luciferin.mappers.category_mapper import map_category
from ff_iii_luciferin.mappers.transaction_mapper import (
    TransactionMapResult,
    map_transaction,
)

logger = logging.getLogger(__name__)


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

    async def _iter_transaction_map_results(
        self,
        *,
        tx_type: str = "withdrawal",
        page_size: int = 1000,
        max_pages: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> AsyncIterator[TransactionMapResult]:
        """
        Iterate over mapped transaction results (domain or rejection reason).

        This is a low-level transport iterator:
        - performs HTTP requests
        - validates OpenAPI DTOs
        - maps DTO -> domain via mapper
        - yields TransactionMapResult
        """
        url = f"{self.base_url}/api/v1/transactions"

        params: dict[str, Any] = {
            "limit": page_size,
            "type": tx_type,
        }

        if start_date:
            params["start"] = start_date.isoformat()
        if end_date:
            params["end"] = end_date.isoformat()

        page = 1

        while True:
            if max_pages is not None and page > max_pages:
                break

            params["page"] = page

            response = await self._request("get", url, params=params)
            data = validate_response_transaction_array(response)

            for tx_dto in data.data:
                yield map_transaction(tx_dto)

            if not data.links.next:
                break

            page += 1

    async def fetch_transactions(
        self,
        *,
        tx_type: str = "withdrawal",
        page_size: int = 1000,
        max_pages: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[SimplifiedTx]:
        """
        Fetch and return all successfully mapped transactions.

        Rejected transactions (multipart / invalid) are silently skipped.
        """
        transactions: list[SimplifiedTx] = []

        async for result in self._iter_transaction_map_results(
            tx_type=tx_type,
            page_size=page_size,
            max_pages=max_pages,
            start_date=start_date,
            end_date=end_date,
        ):
            if result.tx is not None:
                transactions.append(result.tx)
            elif result.reason == "multipart":
                logger.warning("Skipping multipart transaction")
            else:
                logger.error("Skipping invalid transaction")

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
            data = validate_response_category_array(response)
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
        return validate_response_single_tx(response, transaction_id)

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
        return validate_response_single_tx(response_put, transaction_id)
