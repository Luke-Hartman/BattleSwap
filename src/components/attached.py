"""Component for entities that are attached to another entity."""

from dataclasses import dataclass

@dataclass
class Attached:
    """Component for entities that are attached to another entity."""
    entity: int
