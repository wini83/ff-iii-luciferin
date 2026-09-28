"""Exercise the public client against a disposable Firefly III instance."""

import asyncio
import os
from datetime import date
from decimal import Decimal

import httpx
import pytest

from ff_iii_luciferin.api import FireflyClient
from ff_iii_luciferin.api.transaction_update import TransactionUpdate

pytestmark = pytest.mark.e2e


def test_live_firefly_client() -> None:
    base_url = os.environ.get("FIREFLY_E2E_URL")
    token = os.environ.get("FIREFLY_E2E_TOKEN")
    if not base_url or not token:
        pytest.skip("Set FIREFLY_E2E_URL and FIREFLY_E2E_TOKEN to run E2E tests")
    assert base_url is not None and token is not None

    async def run() -> None:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }
        async with httpx.AsyncClient(base_url=base_url, headers=headers) as setup:
            category_response = await setup.post(
                "/api/v1/categories", json={"name": "E2E groceries"}
            )
            category_response.raise_for_status()
            category_id = int(category_response.json()["data"]["id"])

            account_response = await setup.post(
                "/api/v1/accounts",
                json={
                    "name": "E2E checking",
                    "type": "asset",
                    "account_role": "defaultAsset",
                },
            )
            assert account_response.is_success, account_response.text
            account_response.raise_for_status()
            account_id = account_response.json()["data"]["id"]

            ids = []
            for index in range(2):
                response = await setup.post(
                    "/api/v1/transactions",
                    json={
                        "apply_rules": False,
                        "transactions": [
                            {
                                "type": "withdrawal",
                                "date": "2025-01-15T12:00:00+00:00",
                                "amount": f"{index + 10}.00",
                                "description": f"E2E purchase {index}",
                                "source_id": account_id,
                                "destination_name": f"E2E shop {index}",
                                "category_id": str(category_id),
                            }
                        ],
                    },
                )
                assert response.is_success, response.text
                response.raise_for_status()
                ids.append(int(response.json()["data"]["id"]))

        client = FireflyClient(base_url, token)
        try:
            categories = await client.fetch_categories(limit=1)
            assert any(item.id == category_id for item in categories)

            first = await client.get_transaction(ids[0])
            assert first.description == "E2E purchase 0"
            assert first.amount == Decimal("10.00")
            assert first.category is not None and first.category.id == category_id

            transactions = await client.fetch_transactions(
                page_size=1,
                start_date=date(2025, 1, 15),
                end_date=date(2025, 1, 15),
            )
            assert set(ids) <= {item.id for item in transactions}

            updated = await client.update_transaction(
                ids[0], TransactionUpdate(description="E2E updated", notes="verified")
            )
            assert updated.description == "E2E updated"
            assert updated.notes == "verified"
            assert (await client.get_transaction(ids[0])).description == "E2E updated"
        finally:
            await client.close()

    asyncio.run(run())
