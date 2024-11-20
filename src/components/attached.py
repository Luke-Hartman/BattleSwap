"""Component for entities that are attached to another entity."""

from dataclasses import dataclass
from typing import Tuple

@dataclass
class Attached:
    """Component for entities that are attached to another entity."""
    entity: int
    remove_on_death: bool
    offset: Tuple[int, int] = (0, 0)
    """The offset of the attached entity from the target's position."""

