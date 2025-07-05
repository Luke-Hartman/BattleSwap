"""ProjectileDamage component module for Battle Swap.

This module contains the ProjectileDamage component, which represents the damage a projectile can deal.
"""

from dataclasses import dataclass
from typing import List, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effects import Effect
    from unit_condition import UnitCondition

@dataclass
class Projectile:
    """Represents a projectile.
    
    A projectile is an entity that moves through space and applies effects when it collides
    with valid targets that satisfy its unit_condition.
    """
    effects: List["Effect"]
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to Projectile effects."""
    unit_condition: "UnitCondition"
    """Condition that determines which units can be hit by the projectile."""
    pierce: int = 0
    """How many targets the projectile can pierce through."""
    hit_entities: Optional[List[int]] = None
    """Entities that have been hit by the projectile.
    
    Used to prevent piercing through the same target multiple times.
    """
