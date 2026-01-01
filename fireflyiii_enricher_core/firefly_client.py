"""Utility client for interacting with the Firefly III API."""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class FireflyAPIError(RuntimeError):
    """Raised when Firefly III API calls fail."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def filter_without_category(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out transactions that already have a category set."""
    return [
        t
        for t in transactions
        if t["attributes"]["transactions"][0].get("category_id") is None
    ]


def filter_single_part(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only transactions that have a single sub-transaction."""
    return [t for t in transactions if len(t["attributes"]["transactions"]) == 1]


def filter_by_description(
    transactions: List[Dict[str, Any]],
    description_filter: str,
    exact_match: bool = True,
) -> List[Dict[str, Any]]:
    """Match transactions whose description matches the filter."""
    filtered = []
    for t in transactions:
        desc = t["attributes"]["transactions"][0]["description"]
        if exact_match and desc.lower() == description_filter.lower():
            filtered.append(t)
        elif not exact_match and description_filter.lower() in desc.lower():
            filtered.append(t)
    return filtered


def filter_without_tag(
    transactions: List[Dict[str, Any]], tag: str
) -> List[Dict[str, Any]]:
    """
    Filters out transactions that contain a specific tag.

    Iterates over a list of transaction dictionaries and returns only those
    that do not include the given tag in their 'tags' field.

    Args:
        transactions (List[Dict[str, Any]]): List of transaction objects (dicts)
        from Firefly.
        tag (str): The tag to exclude from the results.

    Returns:
        List[Dict[str, Any]]: Filtered list of transactions without the specified tag.
    """
    filtered: List[Dict[str, Any]] = []
    for tx in transactions:
        if tag not in tx["attributes"]["transactions"][0]["tags"]:
            filtered.append(tx)
    return filtered


def simplify_transactions(transactions: List[Dict[str, Any]]) -> List["SimplifiedTx"]:
    """Convert the raw API response into a flat structure."""
    simplified = []
    for t in transactions:
        sub = t["attributes"]["transactions"][0]
        tx_date = datetime.fromisoformat(sub["date"]).date()
        simplified.append(
            SimplifiedTx(
                id=t["id"],
                description=sub["description"],
                amount=float(sub["amount"]),
                date=tx_date,
                tags=sub.get("tags", ""),
                notes=sub.get("notes", ""),
                category=sub.get("category", ""),
            )
        )
    return simplified


@dataclass(eq=False)
class SimplifiedItem:
    """Representation of a simplified transaction item."""

    date: date
    amount: float

    def compare_amount(self, amount: float) -> bool:
        """Return ``True`` if the amounts are equal ignoring their sign."""
        return abs(float(self.amount)) == abs(float(amount))

    def compare(self, other: Any) -> bool:
        """Return ``True`` if ``other`` has the same date and amount."""
        if not isinstance(other, SimplifiedItem):
            return False
        return self.date == other.date and self.compare_amount(other.amount)


@dataclass
class SimplifiedTx(SimplifiedItem):
    """Simplified representation of a Firefly III transaction."""

    id: str
    description: str
    tags: List[str]
    notes: str
    category: str


@dataclass
class SimplifiedCategory:
    """Simplified representation of a Firefly III Category."""

    id: str
    name: str

    @classmethod
    def from_api_dict(cls, category_raw: dict[str, Any]) -> "SimplifiedCategory":
        """Create instance of SimplifiedCategory from raw api dict"""
        category_id = category_raw.get("id", "")
        attributes = category_raw.get("attributes", {})
        name = attributes.get("name", "")
        return cls(id=category_id, name=name)


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
    ) -> List[Dict[str, Any]]:
        """Retrieve transactions of the given type."""
        url = f"{self.base_url}/api/v1/transactions"
        params = {"limit": limit, "type": tx_type}
        if start_date:
            params["start"] = start_date.isoformat()
        if end_date:
            params["end"] = end_date.isoformat()
        page = 1
        transactions: List[Dict[str, Any]] = []

        while True:
            params["page"] = page
            response = await self._request("get", url, params=params)
            data = response
            transactions.extend(data["data"])
            if not data["links"].get("next"):
                break
            page += 1
        return transactions

    async def fetch_categories(
        self, limit: int = 1000, simplified: bool = False
    ) -> List[Dict[str, Any]] | List[SimplifiedCategory]:
        """
        Retrieve categories from Firefly III with optional simplification.

        Fetches categories from Firefly III via paginated requests until all available
        categories are retrieved or the specified limit is reached. Categories can be
        returned either as raw dictionaries or simplified into instances of
        `SimplifiedCategory`.

        Args:
            limit (int, optional): Maximum number of categories to retrieve.
                                    Defaults to 1000.
            simplified (bool, optional): Determines the format of the returned data.
                                        If `True`,
                                        returns a list of `SimplifiedCategory` instances
                                        if `False`,
                                        returns raw API data. Defaults to `False`.

        Returns:
            List[Dict[str, Any]] | List[SimplifiedCategory]: A list of category
            data either in raw dictionary form or as simplified objects.

        Examples:
            client.fetch_categories(limit=50)
            [{"id": "1", "attributes": {...}}, ...]

            client.fetch_categories(simplified=True)
            [SimplifiedCategory(id="1", name="Food"), ...]

        Raises:
            HTTPError: If the request to Firefly III fails.
            KeyError: If the response data format is unexpected.
        """
        url = f"{self.base_url}/api/v1/categories"
        params = {"limit": limit}
        page = 1
        categories: List[Dict[str, Any]] = []

        while True:
            params["page"] = page
            response = await self._request("get", url, params=params)
            data = response
            categories.extend(data["data"])
            if not data["links"].get("next"):
                break
            page += 1
        if not simplified:
            return categories
        result: List[SimplifiedCategory] = []
        for category in categories:
            result.append(SimplifiedCategory.from_api_dict(category))
        return result

    async def update_transaction_description(
        self, transaction_id: int, new_description: str
    ) -> Any:
        """Change the description field for a given transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        old_desc = response.get("data", {}).get("attributes", {})
        old_desc = old_desc.get("transactions", [{}])[0].get("description", {})
        if new_description in old_desc:
            raise RuntimeError("New data is identical to the current one.")
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"description": new_description}],
        }
        response_put = await self._request("put", url, json=payload)
        return response_put

    async def update_transaction_notes(
        self, transaction_id: int, new_notes: str
    ) -> Any:
        """Replace the notes for a given transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        old_notes = response.get("data", {}).get("attributes", {})
        old_notes = old_notes.get("transactions", [{}])[0].get("notes", "")
        old_notes = old_notes or ""
        if new_notes in old_notes:
            raise RuntimeError("New data is identical to the current one.")
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"notes": new_notes}],
        }
        response = await self._request("put", url, json=payload)
        return response

    async def assign_transaction_category(
        self, transaction_id: int, new_category_id: int
    ) -> Any:
        """Replace the notes for a given transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        attributes = response.get("data", {}).get("attributes", {})
        old_category = attributes.get("transactions", [{}])[0].get("category_id", "")
        if old_category is not None:
            if old_category == str(new_category_id):
                raise RuntimeError("New data is identical to the current one.")
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"category_id": str(new_category_id)}],
        }
        response = await self._request("put", url, json=payload)
        return response

    async def add_tag_to_transaction(self, transaction_id: int, new_tag: str) -> Any:
        """Attach a tag to the specified transaction."""
        url = f"{self.base_url}/api/v1/transactions/{transaction_id}"
        response = await self._request("get", url)
        existing_data = response
        old_sub_transactions = (
            existing_data.get("data", {}).get("attributes", {}).get("transactions", [])
        )
        if len(old_sub_transactions) != 1:
            raise RuntimeError("Transaction is not single part")
        old_sub_tx = old_sub_transactions[0]
        tags = old_sub_tx.get("tags", [])
        if new_tag not in tags:
            tags.append(new_tag)
        payload = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{"tags": tags}],
        }
        await self._request("put", url, json=payload)
        return response
