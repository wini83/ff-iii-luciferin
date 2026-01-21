from types import SimpleNamespace

import pytest

from ff_iii_luciferin.api.errors import FireflyAPIError
from ff_iii_luciferin.mappers.category_mapper import map_category


def test_map_category_missing_attributes_raises() -> None:
    category = SimpleNamespace(id="1", attributes=None)
    with pytest.raises(FireflyAPIError, match="missing attributes"):
        map_category(category)


def test_map_category_invalid_id_raises() -> None:
    category = SimpleNamespace(id="bad", attributes=SimpleNamespace(name="Food"))
    with pytest.raises(FireflyAPIError, match="invalid id"):
        map_category(category)
