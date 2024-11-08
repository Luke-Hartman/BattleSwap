"""ProjectileDamage component module for Battle Swap.

This module contains the ProjectileDamage component, which represents the damage a projectile can deal.
"""

from dataclasses import dataclass
from typing import Optional
from components.aoe import AoEEffect
from visuals import Visual

class ProjectileEffect:
    """Represents the effect a projectile can have."""

@dataclass
class DamageProjectile(ProjectileEffect):
    """Projectile deals damage to a target."""
    damage: int

@dataclass
class AoEProjectile(ProjectileEffect):
    """Projectile creates an AoE when it hits a target.
    
    Note that the stats are handled in entities/effects.py.
    """
    effect: AoEEffect
    """The AoE effect of the projectile."""
    visual: Visual
    """The visual of the AoE."""
    duration: float
    """The duration of the AoE."""
    scale: float
    """The scale of the AoE."""

@dataclass
class Projectile:
    """Represents a projectile."""
    effect: ProjectileEffect
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to Projectile effects."""
