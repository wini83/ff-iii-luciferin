from typing import Any

from pydantic import ValidationError

from ff_iii_luciferin.api.errors import FireflyAPIError
from ff_iii_luciferin.domain.models import SimplifiedTx, SystemInfo
from ff_iii_luciferin.mappers.transaction_mapper import map_transaction
from ff_iii_luciferin.openapi.openapi_client.models.category_array import (
    CategoryArray,
)
from ff_iii_luciferin.openapi.openapi_client.models.system_info import (
    SystemInfo as SystemInfoDTO,
)
from ff_iii_luciferin.openapi.openapi_client.models.transaction_array import (
    TransactionArray,
)
from ff_iii_luciferin.openapi.openapi_client.models.transaction_single import (
    TransactionSingle,
)


def validate_response_about(response: Any) -> SystemInfo:
    try:
        dto = SystemInfoDTO.model_validate(response)
    except ValidationError as exc:
        raise FireflyAPIError("Invalid response schema for system information") from exc
    if dto.data is None:
        raise FireflyAPIError("Missing data in system information response")
    return SystemInfo(
        version=dto.data.version,
        api_version=dto.data.api_version,
        php_version=dto.data.php_version,
        os=dto.data.os,
        driver=dto.data.driver,
    )


def validate_response_single_tx(response: Any, transaction_id: int) -> SimplifiedTx:
    try:
        dto = TransactionSingle.model_validate(response)
    except ValidationError as exc:
        raise FireflyAPIError(
            f"Invalid response schema for transaction {transaction_id}"
        ) from exc
    map_result = map_transaction(dto.data)
    if isinstance(map_result.tx, SimplifiedTx):
        return map_result.tx
    if map_result.reason == "multipart":
        raise FireflyAPIError(
            f"Transaction {transaction_id} is multipart and not supported"
        )
    raise FireflyAPIError(
        f"Transaction {transaction_id} could not be mapped (invalid DTO)"
    )


def validate_response_transaction_array(response: Any) -> TransactionArray:
    try:
        dto = TransactionArray.model_validate(response)
        return dto
    except ValidationError as exc:
        raise FireflyAPIError("Invalid response schema for transaction array") from exc


def validate_response_category_array(response: Any) -> CategoryArray:
    try:
        dto = CategoryArray.model_validate(response)
        return dto
    except ValidationError as exc:
        raise FireflyAPIError("Invalid response schema for category array") from exc
