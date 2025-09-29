"""Components for effects that trigger when an entity gets a kill."""

from dataclasses import dataclass
from typing import List


@dataclass
class OnKillEffects:
    """Component for units that have effects when they kill another unit."""
    
    effects: List["Effect"]
    """The effects to apply when the unit kills another unit."""
