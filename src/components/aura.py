"""Components for aura effects."""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Type
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effects import Effect
    from unit_condition import UnitCondition

@dataclass
class Aura:
    """Individual aura attached to a unit."""
    owner: int
    radius: float
    effects: List["Effect"]
    color: Tuple[int, int, int]
    period: float
    owner_condition: "UnitCondition"
    unit_condition: "UnitCondition"
    duration: float = float('inf')
    time_elapsed: float = 0

@dataclass
class Auras:
    """Collection of auras attached to a unit."""
    auras: List[Aura] = field(default_factory=list)

