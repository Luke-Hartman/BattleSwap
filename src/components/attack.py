"""Attack component module for Battle Swap.

This module contains the Attack component, which represents the attack properties of a unit.
"""

from dataclasses import dataclass

@dataclass
class Attack:
    """Represents the attack properties of a unit."""

    range: float
    """The attack range of the unit, in pixels."""

    damage: int
    """The amount of damage the unit deals with each attack."""
