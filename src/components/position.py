"""
Position component module for Battle Swap.

This module contains the Position component, which represents the position of an entity in the game world.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Position:
    """
    Represents the position of an entity in the game world.

    Attributes:
        x (int): The x-coordinate of the entity's position, in pixels.
        y (int): The y-coordinate of the entity's position, in pixels.
    """
    x: int
    """The x-coordinate of the entity's position, in pixels."""

    y: int
    """The y-coordinate of the entity's position, in pixels."""

    def distance(self, other: 'Position', y_bias: Optional[float]) -> float:
        """Calculate the distance to another position."""
        if y_bias is not None:
            return ((self.x - other.x) ** 2 + ((self.y - other.y) * y_bias) ** 2) ** 0.5
        else:
            return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
