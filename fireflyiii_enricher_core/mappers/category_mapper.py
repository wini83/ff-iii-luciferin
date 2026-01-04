from fireflyiii_enricher_core.domain.models import SimplifiedCategory
from fireflyiii_enricher_core.openapi.openapi_client.models.category_read import (
    CategoryRead,
)


def map_category(category: CategoryRead) -> SimplifiedCategory:
    attrs = category.attributes
    assert attrs is not None
    return SimplifiedCategory(id=category.id, name=attrs.name)
