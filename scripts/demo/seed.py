"""Seed a persistent local Firefly III instance with deterministic demo records."""

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = os.environ["FIREFLY_URL"].rstrip("/")
TOKEN = os.environ["FIREFLY_TOKEN"]


def request(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    body = json.dumps(payload).encode() if payload is not None else None
    req = Request(
        BASE_URL + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
    )
    try:
        with urlopen(req, timeout=30) as response:
            result: dict[str, Any] = json.load(response)
            return result
    except HTTPError as exc:
        raise RuntimeError(
            f"Firefly III {method} {path} returned {exc.code}: "
            f"{exc.read().decode(errors='replace')}"
        ) from exc


def list_all(path: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    page = 1
    while True:
        query = urlencode({**(params or {}), "limit": "100", "page": str(page)})
        result = request("GET", f"{path}?{query}")
        records.extend(result["data"])
        if not result.get("links", {}).get("next"):
            return records
        page += 1


def ensure_named(
    path: str,
    name: str,
    payload: dict[str, Any],
    existing: list[dict[str, Any]],
) -> str:
    for record in existing:
        if record["attributes"]["name"] == name:
            return str(record["id"])
    record = request("POST", path, payload)["data"]
    existing.append(record)
    return str(record["id"])


def main() -> None:
    categories = list_all("/api/v1/categories")
    category_ids = {
        name: ensure_named("/api/v1/categories", name, {"name": name}, categories)
        for name in ("Demo groceries", "Demo transport", "Demo subscriptions")
    }

    accounts = list_all("/api/v1/accounts", {"type": "asset"})
    account_ids = {
        name: ensure_named(
            "/api/v1/accounts",
            name,
            {"name": name, "type": "asset", "account_role": "defaultAsset"},
            accounts,
        )
        for name in ("Demo checking", "Demo savings")
    }

    existing = {
        split.get("external_id")
        for group in list_all("/api/v1/transactions")
        for split in group["attributes"]["transactions"]
    }
    today = datetime.now(UTC).date()
    checking = account_ids["Demo checking"]
    savings = account_ids["Demo savings"]
    rows: list[
        tuple[
            str,
            str,
            str,
            str,
            str | None,
            str | None,
            str | None,
            str | None,
            list[str],
        ]
    ] = [
        (
            "groceries",
            "withdrawal",
            "12.50",
            "Corner shop",
            checking,
            None,
            "Demo corner shop",
            category_ids["Demo groceries"],
            ["demo", "food"],
        ),
        (
            "transport",
            "withdrawal",
            "4.80",
            "Bus ticket",
            checking,
            None,
            "Demo transit",
            category_ids["Demo transport"],
            ["demo", "travel"],
        ),
        (
            "subscription",
            "withdrawal",
            "9.99",
            "Music subscription",
            checking,
            None,
            "Demo streaming",
            category_ids["Demo subscriptions"],
            ["demo", "recurring"],
        ),
        (
            "uncategorized",
            "withdrawal",
            "7.25",
            "Uncategorized purchase",
            checking,
            None,
            "Demo kiosk",
            None,
            ["demo"],
        ),
        (
            "deposit",
            "deposit",
            "250.00",
            "Demo income",
            None,
            checking,
            "Demo employer",
            None,
            ["demo", "income"],
        ),
        (
            "transfer",
            "transfer",
            "50.00",
            "Savings transfer",
            checking,
            savings,
            None,
            None,
            ["demo", "transfer"],
        ),
    ]
    created = 0
    for index, (
        key,
        tx_type,
        amount,
        description,
        source_id,
        destination_id,
        other_name,
        category_id,
        tags,
    ) in enumerate(rows):
        external_id = f"ff-iii-luciferin-demo-{key}"
        if external_id in existing:
            continue
        split: dict[str, Any] = {
            "type": tx_type,
            "date": (today - timedelta(days=index)).isoformat() + "T12:00:00+00:00",
            "amount": amount,
            "description": description,
            "external_id": external_id,
            "tags": tags,
            "notes": "Seeded by ff-iii-luciferin for manual testing",
        }
        if source_id:
            split["source_id"] = source_id
        else:
            split["source_name"] = other_name
        if destination_id:
            split["destination_id"] = destination_id
        else:
            split["destination_name"] = other_name
        if category_id:
            split["category_id"] = category_id
        request(
            "POST",
            "/api/v1/transactions",
            {"apply_rules": False, "transactions": [split]},
        )
        created += 1

    sys.stdout.write(
        f"Demo seed ready: {len(category_ids)} categories, "
        f"{len(account_ids)} accounts, {len(rows)} transactions "
        f"({created} newly created).\n"
    )


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        sys.stderr.write(f"Demo seed failed: {exc}\n")
        sys.exit(1)
