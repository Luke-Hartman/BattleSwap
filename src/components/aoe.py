"""Component for area of effect abilities.

This module contains components for different types of area of effect (AoE) abilities.
There are two main types:
1. VisualAoE - an entity that affects other entities which collide with it using pixel-perfect collision 
   detection and has a visual representation.
2. CircleAoE - an entity that affects other entities within a specified radius without a visual representation
   that hits instantly.

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
class VisualAoE:
    """The VisualAoE component for pixel-based collision with visual representation."""

    effects: List["Effect"]
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to AoE effects."""
    unit_condition: "UnitCondition"
    """Condition that determines which units are affected by the AoE."""
    hit_entities: List[int] = field(default_factory=list)
    """Entities that have already been hit by the AoE."""

@dataclass
class CircleAoE:
    """The CircleAoE component for radius-based collision without visual representation."""

    effects: List["Effect"]
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to AoE effects."""
    unit_condition: "UnitCondition"
    """Condition that determines which units are affected by the AoE."""
    radius: float
    """The radius to use for collision detection."""
