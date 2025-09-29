"""VolleyProjectile component module for Battle Swap.

This module contains the VolleyProjectile component, which represents a projectile
that flies in from a fixed angle and distance to hit a specific target location.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VolleyProjectile:
    """Represents a volley projectile.
    
    A volley projectile is an entity that flies in from a fixed angle and distance
    to hit a specific target location, then applies effects when it lands.
    """
    effects: List["Effect"]
    """Effects to apply when the projectile lands."""
    
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to VolleyProjectile effects."""
    
    target_x: float
    """X coordinate where the projectile will land."""
    
    target_y: float
    """Y coordinate where the projectile will land."""
    
    speed: float
    """Speed of the projectile."""