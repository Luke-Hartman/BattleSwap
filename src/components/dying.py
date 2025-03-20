"""Component for units that are dying.

This is just to allow units to finish their current frame before dying.

This allows mirroring units to both kill each other at the same time.
"""

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from unit_condition import UnitCondition

if TYPE_CHECKING:
    from effects import Effect

@dataclass
class Dying:
    """Component for units that are dying."""

@dataclass
class OnDeathEffect:
    """Component for units that have effects when they die."""
    
    effects: List["Effect"]
    """The effects to apply when the unit dies."""
    
    condition: Optional[UnitCondition] = None
    """Optional condition that must be met for the effects to be applied."""
