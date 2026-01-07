from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TransactionUpdate:
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[int] = None
