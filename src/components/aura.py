"""Components for aura effects."""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effects import Effect

@dataclass
class Aura:
    """Aura component."""
    radius: int
    effects: List["Effect"]
    color: Tuple[int, int, int]
    period: float
    hits_owner: bool
    hits_allies: bool
    hits_enemies: bool
    last_triggered: float = field(default_factory=lambda: float("-inf"))

