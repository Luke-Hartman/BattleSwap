"""Component for area of effect abilities.

The primary difference between an AoE and an Aura, is than an AoE is an entity that
affects other entities which collide with it, while an Aura is a continuous effect
that affects entities in a radius of another entity.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from effects import Effect
    from unit_condition import UnitCondition

@dataclass
class AoE:
    """The AoE component."""

    effects: List["Effect"]
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to AoE effects."""
    unit_condition: "UnitCondition"
    """Condition that determines which units are affected by the AoE."""
    hit_entities: List[int] = field(default_factory=list)
    """Entities that have already been hit by the AoE."""
