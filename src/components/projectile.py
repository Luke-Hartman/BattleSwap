"""ProjectileDamage component module for Battle Swap.

This module contains the ProjectileDamage component, which represents the damage a projectile can deal.
"""

from dataclasses import dataclass
from typing import List, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effects import Effect

@dataclass
class Projectile:
    """Represents a projectile."""
    effects: List["Effect"]
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to Projectile effects."""
