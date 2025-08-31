"""Repeat component for continually applying effects at intervals."""

from dataclasses import dataclass
from typing import List, Optional
from unit_condition import UnitCondition

@dataclass
class Repeat:
    """Component that continually repeats effects at an interval until a stop condition is met."""

    effects: List['Effect']
    """The effects to repeat."""
    
    interval: float
    """The interval between effect applications in seconds."""
    
    stop_condition: UnitCondition
    """The condition that, when met, stops the repeating effects."""
    
    time_since_creation: float = 0.0
    """Time since the component was created."""
    
    owner: Optional[int] = None
    """The owner of the effect (for applying effects)."""
    
    parent: Optional[int] = None
    """The parent entity (for applying effects)."""
    
    target: Optional[int] = None
    """The target entity (for applying effects)."""
