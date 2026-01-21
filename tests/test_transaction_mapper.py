from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from ff_iii_luciferin.api.openapi_types import (
    TransactionTypeProperty,
)
from ff_iii_luciferin.domain.models import (
    Currency,
    FXContext,
    SimplifiedCategory,
    TxType,
)
from ff_iii_luciferin.mappers.transaction_mapper import (
    TransactionMapResult,
    map_transaction,
)
from ff_iii_luciferin.openapi.openapi_client.models.transaction import (
    Transaction,
)
from ff_iii_luciferin.openapi.openapi_client.models.transaction_read import (
    TransactionRead,
)


def make_transaction_read_from_split(split_dict: dict[str, Any]) -> TransactionRead:
    tx = Transaction.model_validate({"transactions": [split_dict]})
    return TransactionRead.model_validate(
        {
            "id": "123",
            "type": "transactions",
            "attributes": tx.model_dump(by_alias=True),  # 🔥 TO JEST FIX
            "links": {},
        }
    )


def test_map_transaction_single_split_happy_path() -> None:
    split_dict = {
        "type": TransactionTypeProperty.WITHDRAWAL,
        "amount": "12.34",
        "date": datetime(2025, 1, 1),
        "description": "Test tx",
        "source_id": "1",
        "destination_id": "2",
        "tags": ["test"],
        "notes": "note",
        "currency_code": "USD",
        "currency_symbol": "$",
        "currency_decimal_places": 2,
        "category_id": "7",
        "category_name": "Food",
    }
    tx = make_transaction_read_from_split(split_dict)

    result = map_transaction(tx)

    assert result == TransactionMapResult(
        tx=result.tx,
        reason=None,
    )
    assert result.tx is not None
    assert result.tx.id == 123
    assert result.tx.description == "Test tx"
    assert result.tx.amount == Decimal("12.34")
    assert result.tx.date.isoformat() == "2025-01-01"
    assert result.tx.tags == ["test"]
    assert result.tx.notes == "note"
    assert result.tx.category == SimplifiedCategory(id=7, name="Food")


def test_map_transaction_maps_currency_and_type() -> None:
    split_dict = {
        "type": TransactionTypeProperty.DEPOSIT,
        "amount": "19.99",
        "date": datetime(2025, 1, 2),
        "description": "Deposit",
        "source_id": "1",
        "destination_id": "2",
        "currency_code": "EUR",
        "currency_symbol": "€",
        "currency_decimal_places": 2,
    }

    tx = make_transaction_read_from_split(split_dict)
    result = map_transaction(tx)

    assert result.reason is None
    assert result.tx is not None
    assert result.tx.currency == Currency(code="EUR", symbol="€", decimals=2)
    assert result.tx.type == TxType.DEPOSIT


def test_map_transaction_maps_fx_context() -> None:
    split_dict = {
        "type": TransactionTypeProperty.WITHDRAWAL,
        "amount": "20.00",
        "date": datetime(2025, 1, 3),
        "description": "FX",
        "source_id": "1",
        "destination_id": "2",
        "currency_code": "USD",
        "currency_symbol": "$",
        "currency_decimal_places": 2,
        "foreign_currency_code": "JPY",
        "foreign_currency_symbol": "¥",
        "foreign_currency_decimal_places": 0,
        "foreign_amount": "3000",
    }

    tx = make_transaction_read_from_split(split_dict)
    result = map_transaction(tx)

    assert result.reason is None
    assert result.tx is not None
    assert result.tx.fx == FXContext(
        original_currency=Currency(code="JPY", symbol="¥", decimals=0),
        original_amount=Decimal("3000"),
    )


def test_map_transaction_rejects_missing_currency() -> None:
    split_dict = {
        "type": TransactionTypeProperty.WITHDRAWAL,
        "amount": "10.00",
        "date": datetime(2025, 1, 1),
        "description": "No currency",
        "source_id": "1",
        "destination_id": "2",
    }

    tx = make_transaction_read_from_split(split_dict)
    result = map_transaction(tx)

    assert result.tx is None
    assert result.reason == "invalid"


def test_map_transaction_rejects_multi_split() -> None:
    split_dict = {
        "type": TransactionTypeProperty.WITHDRAWAL,
        "amount": "10.00",
        "date": datetime(2025, 1, 1),
        "description": "Split",
        "source_id": "1",
        "destination_id": "2",
    }

    tx = Transaction.model_validate(
        {
            "transactions": [split_dict, split_dict],
        }
    )

    tx_read = TransactionRead.model_validate(
        {
            "id": "999",
            "type": "transactions",
            "attributes": tx.model_dump(by_alias=True),  # 🔥 I TU
            "links": {},
        }
    )

    result = map_transaction(tx_read)
    assert result.tx is None
    assert result.reason == "multipart"


def test_map_transaction_rejects_missing_date() -> None:
    tx_read = SimpleNamespace(
        id="123",
        attributes=SimpleNamespace(
            transactions=[SimpleNamespace(var_date=None)],
        ),
    )

    result = map_transaction(tx_read)
    assert result.tx is None
    assert result.reason == "invalid"


def test_map_transaction_rejects_invalid_id() -> None:
    split = SimpleNamespace(
        var_date=datetime(2025, 1, 1),
        amount="10.00",
        description="Test",
        tags=[],
        notes=None,
        category_name=None,
    )
    tx_read = SimpleNamespace(
        id="not-an-int",
        attributes=SimpleNamespace(transactions=[split]),
    )

    result = map_transaction(tx_read)
    assert result.tx is None
    assert result.reason == "invalid"
