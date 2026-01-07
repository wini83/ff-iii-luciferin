from ff_iii_luciferin.openapi.openapi_client.models.transaction_read import (
    TransactionRead,
)


def test_transaction_read_can_be_validated() -> None:
    payload = {
        "id": "123",
        "type": "transactions",
        "attributes": {
            "transactions": [
                {
                    "type": "withdrawal",
                    "amount": "12.34",
                    "date": "2025-01-01",
                    "description": "Test tx",
                    "source_id": "1",  # REQUIRED
                    "destination_id": "2",  # REQUIRED
                    "tags": ["test"],
                    "notes": "note",
                    "category_name": "Food",
                }
            ]
        },
        "links": {},
    }

    tx = TransactionRead.model_validate(payload)

    assert tx.id == "123"
