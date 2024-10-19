"""Attack components module for Battle Swap.

This module contains the MeleeAttack and ProjectileAttack components,
which represent different types of attacks for units.
"""

import math
from dataclasses import dataclass
from enum import Enum, auto

class ProjectileType(Enum):
    ARROW = auto()
    FIREBALL = auto()

@dataclass
class MeleeAttack:
    """Represents a melee attack."""

    range: float
    """The range of the melee attack, in pixels."""

    damage: int
    """The amount of damage the melee attack deals."""

    attack_angle: float = math.pi / 3
    """Attack angle in radians (default: 60 degrees)"""

@dataclass
class ProjectileAttack:
    """Represents a projectile attack."""

    range: float
    """The range of the projectile attack, in pixels."""

    damage: int
    """The amount of damage the projectile attack deals."""

    projectile_speed: float
    """The speed of the projectile, in pixels per second."""

    projectile_type: ProjectileType
    """The type of projectile to use for the attack."""

    projectile_offset_x: float
    """The x offset of the projectile, in pixels."""

    projectile_offset_y: float
    """The y offset of the projectile, in pixels."""
