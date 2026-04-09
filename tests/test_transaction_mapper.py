from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from ff_iii_luciferin.api.openapi_types import (
    TransactionTypeProperty,
)
from ff_iii_luciferin.domain.models import (
    AccountType,
    Currency,
    FXContext,
    SimplifiedAccountRef,
    SimplifiedCategory,
    TxType,
)
from ff_iii_luciferin.mappers.transaction_mapper import (
    TransactionMapResult,
    map_account_ref,
    map_account_type,
    map_currency,
    map_fx_context,
    map_transaction,
    map_tx_type,
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


def test_map_transaction_maps_accounts() -> None:
    split_dict = {
        "type": TransactionTypeProperty.TRANSFER,
        "amount": "19.99",
        "date": datetime(2025, 1, 2),
        "description": "Transfer",
        "source_id": "1",
        "source_name": "Main account",
        "source_iban": "PL001",
        "source_type": "Asset account",
        "destination_id": "2",
        "destination_name": "Mortgage",
        "destination_iban": "PL002",
        "destination_type": "Mortgage",
        "currency_code": "EUR",
        "currency_symbol": "€",
        "currency_decimal_places": 2,
    }

    tx = make_transaction_read_from_split(split_dict)
    result = map_transaction(tx)

    assert result.reason is None
    assert result.tx is not None
    assert result.tx.source_account == SimplifiedAccountRef(
        id=1,
        name="Main account",
        type=AccountType.ASSET,
        iban="PL001",
    )
    assert result.tx.destination_account == SimplifiedAccountRef(
        id=2,
        name="Mortgage",
        type=AccountType.MORTGAGE,
        iban="PL002",
    )


def test_map_account_type_maps_liability_variants() -> None:
    assert map_account_type("Liability account") == AccountType.LIABILITY
    assert map_account_type("liability") == AccountType.LIABILITY
    assert map_account_type("liabilities") == AccountType.LIABILITY


def test_map_account_ref_returns_none_for_invalid_values() -> None:
    assert map_account_ref("bad", "Account", "Asset account", "PL001") is None
    assert map_account_ref("1", "Account", "Unknown", "PL001") is None


def test_map_account_ref_preserves_missing_iban_as_none() -> None:
    assert map_account_ref(
        "1",
        "Account",
        "Asset account",
        None,
    ) == SimplifiedAccountRef(
        id=1,
        name="Account",
        type=AccountType.ASSET,
        iban=None,
    )


def test_map_currency_returns_none_when_incomplete() -> None:
    split = make_transaction_read_from_split(
        {
            "type": TransactionTypeProperty.WITHDRAWAL,
            "amount": "12.34",
            "date": datetime(2025, 1, 1),
            "description": "Test tx",
            "source_id": "1",
            "destination_id": "2",
            "currency_code": "USD",
            "currency_decimal_places": 2,
        }
    ).attributes.transactions[0]

    assert map_currency(split) is None


def test_map_fx_context_returns_none_for_invalid_foreign_amount() -> None:
    split = make_transaction_read_from_split(
        {
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
            "foreign_amount": "bad",
        }
    ).attributes.transactions[0]

    assert map_fx_context(split) is None


def test_map_fx_context_returns_none_when_foreign_currency_is_incomplete() -> None:
    split = make_transaction_read_from_split(
        {
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
            "foreign_amount": "3000",
        }
    ).attributes.transactions[0]

    assert map_fx_context(split) is None


def test_map_tx_type_returns_none_for_invalid_value() -> None:
    assert map_tx_type("unknown") is None


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


def test_map_transaction_ignores_invalid_category_id() -> None:
    split_dict = {
        "type": TransactionTypeProperty.WITHDRAWAL,
        "amount": "12.34",
        "date": datetime(2025, 1, 1),
        "description": "Test tx",
        "source_id": "1",
        "destination_id": "2",
        "currency_code": "USD",
        "currency_symbol": "$",
        "currency_decimal_places": 2,
        "category_id": "bad",
        "category_name": "Food",
    }

    tx = make_transaction_read_from_split(split_dict)
    result = map_transaction(tx)

    assert result.reason is None
    assert result.tx is not None
    assert result.tx.category is None


def test_map_transaction_rejects_invalid_type() -> None:
    tx_read = SimpleNamespace(
        id="123",
        attributes=SimpleNamespace(
            transactions=[
                SimpleNamespace(
                    var_date=datetime(2025, 1, 1),
                    amount="10.00",
                    type="invalid",
                )
            ],
        ),
    )

    result = map_transaction(tx_read)
    assert result.tx is None
    assert result.reason == "invalid"
