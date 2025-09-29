"""Components for effects that trigger when an entity hits another entity."""

from dataclasses import dataclass
from typing import List


@dataclass
class OnHitEffects:
    """Component for units that have effects when they hit another unit."""
    
    effects: List["Effect"]
    """The effects to apply when the unit hits another unit."""
