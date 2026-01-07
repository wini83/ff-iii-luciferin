"""
OpenAPI generated client (vendor code).

Compatibility shim: exposes this package as `openapi_client`.
DO NOT import from domain or business logic.
"""

import sys
import ff_iii_luciferin.openapi.openapi_client as _openapi_client

sys.modules["openapi_client"] = _openapi_client
