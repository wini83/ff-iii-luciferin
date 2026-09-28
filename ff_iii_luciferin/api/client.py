"""Utility client for interacting with the Firefly III API."""

import logging
from collections.abc import AsyncIterator
from datetime import date
from typing import Any

import httpx

from ff_iii_luciferin.api.errors import FireflyAPIError
from ff_iii_luciferin.api.transaction_update import TransactionUpdate
from ff_iii_luciferin.api.validators import (
    validate_response_about,
    validate_response_category_array,
    validate_response_single_tx,
    validate_response_transaction_array,
)
from ff_iii_luciferin.domain.models import SimplifiedCategory, SimplifiedTx, SystemInfo
from ff_iii_luciferin.mappers.category_mapper import map_category
from ff_iii_luciferin.mappers.transaction_mapper import (
    TransactionMapResult,
    map_transaction,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=60.0,
    write=30.0,
    pool=10.0,
)


class FireflyClient:
    """Async client for the supported Firefly III endpoints.

    Pass the instance root URL without ``/api/v1`` and a personal access
    token. Always call :meth:`close` when finished, typically in a ``finally``
    block. Listing methods return handwritten domain models; the generated
    OpenAPI transport models remain internal.

    Args:
        base_url: Firefly III instance root, for example
            ``https://firefly.example``. A trailing slash is accepted.
        token: Personal access token sent as a bearer token.
    """

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }
        transport = httpx.AsyncHTTPTransport(retries=2)
        self._client = httpx.AsyncClient(
            headers=self.headers, timeout=DEFAULT_TIMEOUT, transport=transport
        )

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
            raise FireflyAPIError(f"Request timed out: {method.upper()} {url}") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise FireflyAPIError(
                f"HTTP error: {exc}", status_code=status_code
            ) from exc
        except httpx.RequestError as exc:
            raise FireflyAPIError(f"Request failed: {exc}") from exc

    async def close(self) -> None:
        """Release the underlying HTTP connections.

        Call this once after the final request. The client does not implement
        an async context manager.
        """
        await self._client.aclose()

    async def get_about(self) -> SystemInfo:
        """Read version and environment information from ``/api/v1/about``.

        Returns:
            System information. Individual fields may be ``None`` when Firefly
            III omits them.

        Raises:
            FireflyAPIError: The request fails or the response is invalid.
        """
        response = await self._request("get", f"{self.base_url}/api/v1/about")
        return validate_response_about(response)

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
            logger.info(
                "Fetching Firefly transactions: page=%s, page_size=%s", page, page_size
            )
            response = await self._request("get", url, params=params)
            data = validate_response_transaction_array(response)

            for tx_dto in data.data:
                yield map_transaction(tx_dto)
            logger.info(
                "Fetched page %s with %s transactions",
                page,
                len(data.data),
            )
            if not data.data:
                logger.warning("Empty page %s, stopping pagination", page)
                break
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
        """Fetch single-split transactions across Firefly III pages.

        Multipart groups and responses that cannot be mapped are logged and
        skipped. The result is therefore not guaranteed to contain every
        transaction group reported by Firefly III. Use
        ``fetch_transactions_with_stats`` to count those skipped groups.

        Args:
            tx_type: Firefly III transaction type filter. Defaults to
                ``"withdrawal"``; ``"deposit"`` and ``"transfer"`` are also
                useful values.
            page_size: Requested number of groups per API page.
            max_pages: Maximum pages to request, or ``None`` to follow
                pagination to the end.
            start_date: Inclusive start date sent to the API, if supplied.
            end_date: Inclusive end date sent to the API, if supplied.

        Returns:
            Successfully mapped transactions in API order.

        Raises:
            FireflyAPIError: A request fails or a page has an invalid schema.
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
    ) -> list[SimplifiedCategory]:
        """Fetch all categories across Firefly III pages.

        Args:
            limit: Requested number of categories per API page.
            simplified: Retained for compatibility; currently ignored. The
                method always returns ``SimplifiedCategory`` objects.

        Returns:
            Mapped categories in API order.

        Raises:
            FireflyAPIError: A request fails or the response is invalid.
        """
        url = f"{self.base_url}/api/v1/categories"
        params: dict[str, Any] = {"limit": limit}
        page = 1
        categories: list[SimplifiedCategory] = []

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
        """Fetch one single-split transaction by Firefly III group ID.

        Args:
            transaction_id: Firefly III transaction group ID.

        Returns:
            The mapped transaction.

        Raises:
            FireflyAPIError: The request or validation fails, or the group
                has multiple splits or cannot be mapped.
        """
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"

        response = await self._request("get", url)
        return validate_response_single_tx(response, transaction_id)

    async def update_transaction(
        self, transaction_id: int, update: TransactionUpdate
    ) -> SimplifiedTx:
        """Update selected fields of a single-split transaction.

        Firefly III rules and webhooks are enabled for this request. Supplying
        ``tags`` replaces the full tag list; use ``build_add_tag_payload`` to
        preserve existing tags while adding one. The returned response must
        still be mappable as a single-split transaction.

        Args:
            transaction_id: Firefly III transaction group ID.
            update: Non-empty selection of description, notes, tags, and/or
                category ID.

        Returns:
            The mapped transaction returned by Firefly III after the update.

        Raises:
            ValueError: No update field was supplied.
            FireflyAPIError: The request or validation fails, or the returned
                transaction cannot be mapped.
        """
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
