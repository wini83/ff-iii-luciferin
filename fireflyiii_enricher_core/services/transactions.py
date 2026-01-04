from typing import List

from fireflyiii_enricher_core.domain.models import SimplifiedTx


def build_add_tag_payload(
    tx: SimplifiedTx,
    tag: str,
) -> List[str]:
    tags = list(tx.tags)

    if tag not in tags:
        tags.append(tag)

    return tags
