"""Position component for the Battle Swap game."""

from dataclasses import dataclass

@dataclass
class Position:
    """Represents the position of an entity in 2D space."""

    x: float = 0.0
    """The x-coordinate of the entity."""

    y: float = 0.0
    """The y-coordinate of the entity."""