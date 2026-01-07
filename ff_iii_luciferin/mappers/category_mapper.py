from ff_iii_luciferin.api.errors import FireflyAPIError
from ff_iii_luciferin.domain.models import SimplifiedCategory
from ff_iii_luciferin.mappers.utils import parse_int
from ff_iii_luciferin.openapi.openapi_client.models.category_read import (
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
