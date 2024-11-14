"""Components for aura effects."""

from dataclasses import dataclass, field
from typing import List, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effects import Effect
    from unit_condition import UnitCondition

@dataclass
class Aura:
    """Aura component."""
    owner: int
    radius: int
    effects: List["Effect"]
    color: Tuple[int, int, int]
    period: float
    unit_condition: "UnitCondition"
    """Condition that determines which units are affected by the aura."""
    last_triggered: float = field(default_factory=lambda: float("-inf"))

