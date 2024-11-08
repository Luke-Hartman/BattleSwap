"""Attack components module for Battle Swap.

This module contains the MeleeAttack and ProjectileAttack components,
which represent different types of attacks for units.
"""

import math
from dataclasses import dataclass

from components.projectile import ProjectileEffect
from visuals import Visual

@dataclass
class MeleeAttack:
    """Represents a melee attack."""

    range: float
    """How close the unit needs to be to the target to attack."""

    damage: int
    """The amount of damage the melee attack deals."""

    attack_angle: float = math.pi / 12
    """Attack angle in radians (default: 15 degrees)"""

@dataclass
class ProjectileAttack:
    """Represents a projectile attack."""

    range: float
    """How close the unit needs to be to the target to attack."""

    projectile_speed: float
    """The speed of the projectile, in pixels per second."""

    projectile_effect: ProjectileEffect
    """The type of projectile to use for the attack."""

    visual: Visual
    """The visual of the projectile."""

    projectile_offset_x: float
    """The x offset of the projectile from the unit position, in pixels.
    
    (Assuming the unit is facing right)
    """

    projectile_offset_y: float
    """The y offset of the projectile, in pixels."""

@dataclass
class HealingAttack:
    """Represents a healing attack."""

    range: float
    """How close the unit needs to be to the target to attack."""

    healing: int
    """The amount of healing the attack deals."""
