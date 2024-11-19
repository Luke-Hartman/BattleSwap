"""
This module contains the Destination component, which represents a destination strategy.
"""

from dataclasses import dataclass
from target_strategy import TargetStrategy

@dataclass
class Destination:
    """Represents a destination strategy."""

    target_strategy: TargetStrategy
    """The target strategy."""

    x_offset: float
    """The x-offset from the target's position that the unit tries to reach.
    
    This is to prevent units from walking directly towards their target.
    Instead, they will try to walk towards their target's position offset
    by this amount towards the side they are already on.
    """
    min_distance: float = 1
    """The unit will stop moving when it is within this distance of the target."""