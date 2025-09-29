"""Components for effects that trigger when an entity dies."""

from dataclasses import dataclass
from typing import List, Optional
from unit_condition import UnitCondition


@dataclass
class OnDeathEffect:
    """Component for entities that have effects when they die."""
    
    effects: List["Effect"]
    """The effects to apply when the entity dies."""
    
    condition: Optional[UnitCondition] = None
    """Optional condition that must be met for the effects to be applied."""
