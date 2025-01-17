from dataclasses import dataclass
from typing import List

@dataclass
class RangeIndicator:
    """Component for displaying one or more range indicators around an entity."""
    ranges: List[float]
