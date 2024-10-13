"""Attack components module for Battle Swap.

This module contains the MeleeAttack and ProjectileAttack components,
which represent different types of attacks for units.
"""

from dataclasses import dataclass

@dataclass
class MeleeAttack:
    """Represents a melee attack."""

    range: float
    """The range of the melee attack, in pixels."""

    damage: int
    """The amount of damage the melee attack deals."""

@dataclass
class ProjectileAttack:
    """Represents a projectile attack."""

    range: float
    """The range of the projectile attack, in pixels."""

    damage: int
    """The amount of damage the projectile attack deals."""
