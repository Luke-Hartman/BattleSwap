"""Movement component module for Battle Swap.

This module contains the Movement component, which represents the movement properties of a unit.
"""

from dataclasses import dataclass

@dataclass
class Movement:
    """Represents the movement properties of a unit."""

    speed: float
    """The movement speed of the unit, in pixels per second."""
