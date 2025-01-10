"""Component for entities that are attached to another entity."""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

@dataclass
class Attached:
    """Component for entities that are attached to another entity."""
    entity: int
    on_death: Optional[Callable[[int], None]] = None
    """The action to take when the attached entity dies."""
    offset: Tuple[int, int] = (0, 0)
    """The offset of the attached entity from the target's position."""

