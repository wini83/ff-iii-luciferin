from fireflyiii_enricher_core.api.errors import FireflyAPIError
from fireflyiii_enricher_core.domain.models import SimplifiedCategory
from fireflyiii_enricher_core.mappers.utils import parse_int
from fireflyiii_enricher_core.openapi.openapi_client.models.category_read import (
    CategoryRead,
)


def map_category(category: CategoryRead) -> SimplifiedCategory:
    attrs = category.attributes
    if attrs is None:
        raise FireflyAPIError(
            f"Invalid category DTO: missing attributes (id={category.id})"
        )
    category_id = parse_int(category.id)
    if category_id is None:
        raise FireflyAPIError(f"Invalid category DTO: invalid id (id={category.id})")
    return SimplifiedCategory(id=category_id, name=attrs.name)
