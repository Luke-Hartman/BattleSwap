"""ProjectileDamage component module for Battle Swap.

This module contains the ProjectileDamage component, which represents the damage a projectile can deal.
"""

from dataclasses import dataclass

@dataclass
class ProjectileDamage:
    """Represents the damage a projectile can deal."""
    damage: int
