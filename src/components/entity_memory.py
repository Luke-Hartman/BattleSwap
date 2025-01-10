from dataclasses import dataclass

@dataclass
class EntityMemory:
    """Component for entities that are remembered."""

    entity: int
    """The entity to remember."""