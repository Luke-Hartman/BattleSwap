"""Health component for the Battle Swap game."""

from dataclasses import dataclass

@dataclass
class Health:
    """Represents the health of an entity."""

    max_health: int
    """The maximum health of the entity."""

    current_health: int = None
    """The current health of the entity."""

    def __post_init__(self):
        if self.current_health is None:
            self.current_health = self.max_health