from datetime import datetime
from decimal import Decimal

from ff_iii_luciferin.api.openapi_types import (
    TransactionTypeProperty,
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


def make_transaction_read() -> TransactionRead:
    split_dict = {
        "type": TransactionTypeProperty.WITHDRAWAL,
        "amount": "12.34",
        "date": datetime(2025, 1, 1),
        "description": "Test tx",
        "source_id": "1",
        "destination_id": "2",
        "tags": ["test"],
        "notes": "note",
        "category_name": "Food",
    }

    tx = Transaction.model_validate(
        {
            "transactions": [split_dict],
        }
    )

    return TransactionRead.model_validate(
        {
            "id": "123",
            "type": "transactions",
            "attributes": tx.model_dump(by_alias=True),  # 🔥 TO JEST FIX
            "links": {},
        }
    )


def test_map_transaction_single_split_happy_path() -> None:
    tx = make_transaction_read()

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
    assert result.tx.category == "Food"


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
