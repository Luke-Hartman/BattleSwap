"""Component for entities that expire after a certain amount of time."""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Expiration:
    """Component for entities that expire after a certain amount of time."""
    time_left: float
    owner: Optional[int] = None
    target: Optional[int] = None
    expiration_effects: List["Effect"] = field(default_factory=list)
