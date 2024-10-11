"""Velocity component for the Battle Swap game."""

from dataclasses import dataclass

@dataclass
class Velocity:
    """Represents the velocity of an entity."""

    dx: float = 0.0
    """The velocity in the x direction."""

    dy: float = 0.0
    """The velocity in the y direction."""