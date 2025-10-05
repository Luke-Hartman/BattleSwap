"""Components for static discharge system."""

from dataclasses import dataclass


@dataclass
class StaticComponent:
    """Component that tracks static buildup for the StaticDischarge item.
    
    Static builds up as the unit moves and is discharged as extra damage when the unit deals damage.
    """
    
    static_charge: float = 0.0
    """The current amount of static charge accumulated."""

    stacks: int = 1
    """The number of stacks of static buildup items the unit has."""