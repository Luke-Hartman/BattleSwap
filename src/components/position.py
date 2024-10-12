"""
Position component module for Battle Swap.

This module contains the Position component, which represents the position of an entity in the game world.
"""

from dataclasses import dataclass

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
