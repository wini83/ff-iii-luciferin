"""
Re-export selected OpenAPI types for infrastructure layer.

DO NOT import this from domain.
"""

from fireflyiii_enricher_core.openapi.openapi_client.models import (
    transaction_type_property as _tx_type,
)

TransactionTypeProperty = _tx_type.TransactionTypeProperty
