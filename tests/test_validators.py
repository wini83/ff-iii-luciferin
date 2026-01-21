import pytest

from ff_iii_luciferin.api.errors import FireflyAPIError
from ff_iii_luciferin.api.validators import (
    validate_response_category_array,
    validate_response_single_tx,
    validate_response_transaction_array,
)


def test_validate_response_single_tx_invalid_schema() -> None:
    with pytest.raises(
        FireflyAPIError, match="Invalid response schema for transaction 123"
    ):
        validate_response_single_tx({}, 123)


def test_validate_response_transaction_array_invalid_schema() -> None:
    with pytest.raises(
        FireflyAPIError, match="Invalid response schema for transaction array"
    ):
        validate_response_transaction_array({})


def test_validate_response_category_array_invalid_schema() -> None:
    with pytest.raises(
        FireflyAPIError, match="Invalid response schema for category array"
    ):
        validate_response_category_array({})
